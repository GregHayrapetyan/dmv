(function() {
    // Fix for Wagtail InlinePanel image chooser not submitting values on save.
    // Saves initial image values and restores them on form submit,
    // unless the user explicitly clicked "Clear choice".

    var cleared = {};
    var savedValues = {};

    // Track "Clear choice" button clicks
    document.addEventListener('click', function(e) {
        var clearBtn = e.target.closest('[data-chooser-action-clear]');
        if (!clearBtn) return;
        var chooser = clearBtn.closest('.image-chooser');
        if (!chooser) return;
        var input = chooser.querySelector('input[type="hidden"]');
        if (input) {
            cleared[input.name] = true;
            // Remove saved value so we don't restore it
            delete savedValues[input.name];
        }
    }, true);

    // Track "Change image" / new selection - remove cleared flag
    document.addEventListener('click', function(e) {
        var chooseBtn = e.target.closest('[data-chooser-action-choose]');
        if (!chooseBtn) return;
        var chooser = chooseBtn.closest('.image-chooser');
        if (!chooser) return;
        var input = chooser.querySelector('input[type="hidden"]');
        if (input) {
            delete cleared[input.name];
        }
    }, true);

    // Periodically save non-empty image chooser values
    function saveCurrentValues() {
        document.querySelectorAll('.image-chooser input[type="hidden"]').forEach(function(input) {
            if (input.value && !cleared[input.name]) {
                savedValues[input.name] = input.value;
            }
        });
    }

    // Also watch for value changes via MutationObserver
    var observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(m) {
            if (m.type === 'attributes' && m.attributeName === 'value') {
                var input = m.target;
                if (input.value && input.closest && input.closest('.image-chooser')) {
                    savedValues[input.name] = input.value;
                    delete cleared[input.name];
                }
            }
        });
        saveCurrentValues();
    });

    function startObserving() {
        observer.observe(document.body, {
            childList: true, subtree: true,
            attributes: true, attributeFilter: ['value']
        });
        saveCurrentValues();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', startObserving);
    } else {
        startObserving();
    }

    // Also poll for values (catches Telepath-rendered forms)
    setInterval(saveCurrentValues, 500);

    // On form submit: restore values that were lost by InlinePanel bug
    document.addEventListener('submit', function(e) {
        if (!e.target.matches || !e.target.matches('form')) return;
        document.querySelectorAll('.image-chooser input[type="hidden"]').forEach(function(input) {
            if (!input.value && savedValues[input.name] && !cleared[input.name]) {
                input.value = savedValues[input.name];
            }
        });
    }, true);
})();
