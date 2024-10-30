function autosizeTextarea() {
    for (const el of document.getElementsByClassName('autosize-textarea')) {
        const textarea = el.getElementsByTagName('textarea')[0];
        const updateDataAttribute = () => {
            el.setAttribute('data-replicated-value', textarea.value);
        };
        updateDataAttribute();
        textarea.addEventListener('input', updateDataAttribute);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    autosizeTextarea();
})