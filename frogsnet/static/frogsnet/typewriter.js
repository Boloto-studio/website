function typewriter(text, element) {
    element.textContent = '';
    let index = 0;
    const tick = () => {
        if (index <= text.length) {
            element.textContent = text.slice(0, index);
            index += 1;
            setTimeout(tick, 18);
        }
    };
    tick();
};

window.typewriter = typewriter;