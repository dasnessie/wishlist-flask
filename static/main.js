function autosizeTextarea() {
    for (const el of document.getElementsByClassName('autosize-textarea')) {
        el.getElementsByTagName('textarea')[0].addEventListener('input', (e) => {
            el.setAttribute('data-replicated-value', e.currentTarget.value);
        })
    }
}

document.addEventListener('DOMContentLoaded', () => {
    autosizeTextarea();
})