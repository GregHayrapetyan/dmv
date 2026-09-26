# MyTestDVM — Cross-Platform Subscriptions Architecture

_Status doc. Covers Web (Stripe), iOS (Apple IAP), and future Android (Google Play Billing)._
_Last updated: 2026-09-26._

---

## 1. Where we are today

There are **three layers** of reality. Keeping them separate matters, because most of the payment work exists only in layer B.

### 1.A — Deployed (what's live in production today)

Derived from the committed code (the branch history, before our uncommitted work).

**Web (Stripe) — fully working:**
- Subscribe (Stripe Checkout), change plan (proration), cancel at period end, reactivate, update payment method, update billing info, Stripe webhooks.
- "Sign in with Apple" exists but that is **authentication (login)**, NOT payments. Do not confuse it with In-App Purchase.

**Backend (Django):**
- `Subscription` model is **one-per-user** (`OneToOneField`), Stripe-only fields, status/period/tier.
- Stripe service + webhooks + subscription API.
- **No `payment_provider` field, no Apple fields** in production yet (they live in an uncommitted migration).

**iOS:** the old Stripe-based build that Apple **rejected** (Guideline 3.1.1). No compliant iOS app is live.

**Android:** does not exist.

### 1.B — Uncommitted local work (this project, branch `ios-iap-support`, NOT deployed)

**Backend (all local):** `apple_iap_service.py`, `apple_iap_views.py`, migration `0017_subscription_apple_iap_fields` (adds `payment_provider` + `apple_*` fields), Apple verify + server-notification routes, settings (Apple config, DEBUG throttle bump, `APPLE_IAP_ALLOW_UNVERIFIED` test bypass), model/serializer edits, tests.

**Web (all local):** `lib/subscription/apple-iap.ts` (+test), `lib/native/platform.ts` (iOS detection), pricing page branches to Apple on iOS, **Item 1** (Apple subs hide Stripe management, show "Manage in the App Store") in `plan-info`, `detail.ts` `payment_provider` + helpers, 6 locale keys, cookie fix, Capacitor deps.

**iOS wrapper (`/Users/gmiranyan/dev/mytestdmv-ios`):** the entire Capacitor app, native `InAppPurchasePlugin.swift` (purchase + restore), `Products.storekit` local test config. ⚠️ **Not a git repository at all** — zero version control. This is a risk to fix.

### 1.C — Target (what we want)

One coherent, account-based subscription system where a user can buy on whichever platform they're on, get access **everywhere**, manage on the platform they bought from, never get double-billed, and where every lifecycle event (renew/cancel/refund/upgrade/lapse) is reflected correctly — and it's ready for Apple approval and a later Android app.

---

## 2. First principles (the rules everything else follows)

1. **Each store owns its own purchases.** Stripe is the source of truth for web purchases, Apple for iOS purchases, Google for Android purchases. Our backend never "owns" a store subscription — it *mirrors* it.
2. **You can only BUY through the platform's own rails.** iOS app → Apple IAP only (Apple forbids Stripe for digital goods). Android app → Google Play Billing only. Web → Stripe. There is no "buy an Apple subscription from the web."
3. **You can only MANAGE (cancel/change/refund) where you bought.** Our server literally cannot cancel an Apple or Google subscription. It can only reflect their status.
4. **The ACCOUNT owns access, not the platform.** Entitlement is attached to the logged-in user, so access is cross-platform. Buy on iOS → you have access on web and Android too.
5. **The backend is the reconciliation hub.** It collects status from all stores and answers exactly one question for the apps: *does this account currently have access?*

---

## 3. The entitlement model (the core design decision)

**Access rule:** a user has access if **any** subscription on their account, from **any** provider, is currently active (or within its paid period, or in billing grace). It's an OR across providers.

### The problem with today's model

`Subscription` is `OneToOneField(user)` — **one row per user**. That silently breaks cross-platform:

> Real failure we already hit in testing: a user had a Stripe subscription, then bought on iOS. The **same row got overwritten** — `payment_provider` flipped to `apple`, the Stripe IDs were nulled. The backend forgot the Stripe subscription, **but Stripe kept billing the card.** → double billing + an orphaned subscription nobody can see.

### Recommended fix (two parts)

**(a) Data model — one row per (user, provider).** Change `Subscription` from one-per-user to **many-per-user, unique per provider** (`unique_together(user, provider)`). Entitlement = OR across the user's rows. This preserves each store's record independently, supports history, and makes the "bought on two platforms" case survivable instead of corrupting data.

**(b) Purchase guard — prevent accidental double-buy.** Before starting any purchase (Stripe checkout, Apple verify, Google), check whether the account already has an active subscription on a **different** provider. If so, block it with a clear message: *"You already have a subscription purchased on {platform}. Manage or cancel it there before subscribing here."*

> These two are the backbone. Everything in §5–§10 assumes them. **This is decision #1 for you (see §11).**

---

## 4. Purchase rules — where you can buy

| Surface | Allowed rail | Forbidden | Why |
|---|---|---|---|
| Web browser | Stripe | — | No store restrictions on the web |
| iOS app | Apple IAP | Stripe (any digital purchase) | Apple Guideline 3.1.1 (the rejection) |
| Android app | Google Play Billing | Stripe (any digital purchase) | Google Play Payments policy |

---

## 5. Cross-platform access scenarios (the "I bought on iOS then went to web" matrix)

Access is always **yes** if entitled (account-level). What changes is **where you can manage** and **what the UI shows**.

| Bought on | On Web | In iOS app | In Android app |
|---|---|---|---|
| **Web (Stripe)** | ✅ access · full Stripe management | ✅ access · **read-only** ("manage on the web", no external link — see §7 anti-steering) | ✅ access · read-only ("manage on the web") |
| **iOS (Apple)** | ✅ access · link to Apple's subscription page (Item 1 ✅) | ✅ access · "Manage in the App Store" | ✅ access · "manage via Apple" (info only) |
| **Android (Google)** | ✅ access · link to Google Play subscriptions | ✅ access · "manage via Google Play" (info only) | ✅ access · "Manage in Google Play" |
| **Nothing** | free / gated | free / gated | free / gated |

**Rule of thumb:** access everywhere; the "manage" control only lights up on the platform that owns the purchase, and points elsewhere for the others.

---

## 6. Lifecycle events — what to handle, per provider

How each event is **detected** and what we **do**. This is the full set the backend must cover.

| Event | Stripe (web) | Apple (iOS) | Google (Android) | What we do |
|---|---|---|---|---|
| Initial purchase | Checkout + webhook | `purchase()` → verify JWS | Billing flow → verify token | Create/activate the provider's row |
| Renewal (auto) | `invoice.paid` webhook | Server Notification `DID_RENEW` ✅ | RTDN `SUBSCRIPTION_RENEWED` | Extend period end |
| Upgrade | change-plan API | within group (immediate+prorated) | offer change | Reflect new tier immediately |
| Downgrade | change-plan API | within group (**next renewal**) | offer change | Reflect at next renewal |
| Cancel (auto-renew off) | `subscription.updated` | `DID_CHANGE_RENEWAL_STATUS` ✅ | RTDN `CANCELED` | Set `cancel_at_period_end`, keep access until end |
| Expire / lapse | `subscription.deleted` | `EXPIRED` ✅ | RTDN `EXPIRED` | Revoke access |
| Payment failed / grace | `invoice.payment_failed` | `DID_FAIL_TO_RENEW` ✅ | RTDN `IN_GRACE_PERIOD` | `past_due`; keep access during grace |
| Refund / chargeback | `charge.refunded` / dispute | `REFUND` / `REVOKE` ✅ | `SUBSCRIPTION_REVOKED` | Revoke access, mark refunded |
| Restore purchases | n/a (login restores) | `Transaction.currentEntitlements` (needs a button) | `queryPurchases()` (button) | Re-link entitlement to account |
| Deferred / Ask-to-Buy / pending | n/a | `.pending` → **`Transaction.updates`** ⚠️ | `PENDING` state | Activate when approved |
| Acknowledge purchase | n/a | `transaction.finish()` | `acknowledge()` **within 3 days or auto-refund** | Finalize the purchase |

✅ = already implemented (local). ⚠️ = **not yet** — this is Item 5 (the `Transaction.updates` gap): deferred/Ask-to-Buy first purchases are currently **lost**, and the notification handler ignores transactions it hasn't seen.

---

## 7. Apple IAP — which concepts we actually need

Answering "there are so many possibilities, which do we include?"

**Must have:**
- Buy, verify signature (JWS → Apple Root CA G3), activate. ✅ done
- Server Notifications V2 for renew / cancel / expire / refund. ✅ done
- `Transaction.updates` listener for deferred/Ask-to-Buy/interrupted + finishing transactions. ❌ Item 5
- Upgrade/downgrade inside one subscription group (Apple does proration/deferral; we just mirror). ✅ mostly

**Should have:**
- **Restore Purchases** button. ❌ Item 6. Purchases belong to the *Apple ID*; if the app is reinstalled or the DB link is lost, Restore re-syncs entitlement to the logged-in account. Less critical because our entitlement is server-side by login, but Apple reviewers expect it for subscription apps.

**Anti-steering (compliance nuance):** in the iOS app, do **not** show tappable links to buy or manage on the web for a Stripe sub — Apple restricts pointing users to outside purchase mechanisms. Show status **read-only** and, at most, plain text ("manage your subscription on our website"). On the **web** it's fine to link to `apps.apple.com/account/subscriptions` (Item 1 already does this).

**Can skip / defer:** Family Sharing, promotional & intro offers, **free trials** (a *business* decision — say if you want them; they change product setup), win-back offers.

**Not a thing:** "delete a subscription." Users cancel (turn off auto-renew); it then lapses at period end. There is no delete.

---

## 8. Stripe (web) — mapping

Concepts map cleanly: Checkout = buy; `customer.subscription` = the sub; proration = upgrade/downgrade; `cancel_at_period_end` = cancel; billing portal / update-payment = manage card; webhooks = the "server notifications" equivalent. Restore isn't needed — logging in restores access. Stripe is the most flexible rail and stays web-only.

---

## 9. Android (Google Play Billing) — when we add it

Shape mirrors Apple, different names:
- Products = **base plans + offers** in Play Console.
- Client: Play Billing Library → launch flow → get a **purchase token**.
- Verify server-side via **Play Developer API**; **must `acknowledge()` within 3 days** or Google auto-refunds.
- Server events via **RTDN** (Real-Time Developer Notifications over Pub/Sub) — the Apple-notifications equivalent.
- Same entitlement model, same cross-platform rules. Adding it later = a new `provider = 'google'`, a verify endpoint, an RTDN webhook, and an Android Capacitor wrapper.

**Design-for-later:** if we build the (user, provider) model now (§3), Android slots in without rework. **This is decision #5.**

---

## 10. The hard cases & conflicts (edge cases to decide)

1. **Double subscription (two providers active).** Prevented by the purchase guard (§3b). If it still happens (edge/race), entitlement = OR (user keeps access), and we surface a "you have two subscriptions" notice with links to cancel one. **Never silently overwrite.**
2. **Switching provider while one is still active.** User cancels Stripe (active until period end) and wants Apple now. Buying Apple immediately = short overlap/double charge. Options: (a) block until the old one lapses, or (b) allow and accept overlap. **Decision #2.**
3. **Refund after switching / refund of an upgrade.** Store notifies → revoke that provider's row; access recomputed from remaining rows.
4. **Grace period / dunning.** Keep access while a renewal is retrying (Apple grace, Stripe `past_due`, Google grace). Recommended: access stays on during grace, revoke on final failure.
5. **Price parity across stores** (generalized Item 2). Each store sets its own price; the card must show the price of *the store the user will actually pay through*. **Decision #3.**
6. **Restore / new device / reinstall.** Covered by Restore buttons + server entitlement by login (§6).
7. **Account sharing / one purchase, many logins.** Entitlement is per-account; store purchase is per Apple/Google ID. If a user logs into a different app account than the one that bought, Restore may not match. Keep purchase↔account link server-side (we store `apple_original_transaction_id`; guard against linking one store txn to two accounts — already done).
8. **Region & currency.** Stores handle currency/tax per region; our CMS price is a single string. Long-term, prefer reading the store's localized price (ties to Decision #3).

---

## 11. Open decisions (need your call)

1. **Data model:** move `Subscription` to one-row-per-(user, provider) + entitlement = OR? _(Strongly recommended.)_
2. **Provider switch policy:** when switching stores, block until the old sub lapses, or allow a short overlap?
3. **Price parity (Item 2):** match prices by hand per store, or have each app read the store's real price?
4. **Free trials / intro offers:** do you want them? (Changes store product setup.)
5. **Android:** committed to it? (Decides how much to design-for-now.)
6. **iOS anti-steering:** confirm we keep in-app management read-only (no external buy/manage links) for non-Apple subs viewed on iOS.

---

## 12. Recommended phasing

- **Phase 0 (foundation):** (a) put the iOS wrapper under git; (b) implement §3 — (user, provider) model + entitlement OR + purchase guard. Everything else depends on this.
- **Phase 1 (iOS launch-ready):** finish code Items 2–6 (price parity, prod URL, security bypass off, `Transaction.updates`, Restore); Apple product setup; sandbox test; submit.
- **Phase 2 (harden):** grace-period UX, double-sub notice, refund flows, observability/logging of provider events.
- **Phase 3 (Android):** Play Console products, Google verify + RTDN, Android wrapper — slots into the Phase 0 model.
