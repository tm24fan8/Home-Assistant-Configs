`${(() => {
    const state = hass?.states[this.config?.entity]?.state || '';

    let bg_color = 'var(--bubble-main-background-color)';
    let red_color = 'var(--error-color)';

    // Main button background
    const mainButton = card?.querySelector('.bubble-button-background');
    if (mainButton) {
        mainButton.style.opacity = '1';
        mainButton.style.backgroundColor = state === 'on' ? red_color : bg_color;
        mainButton.style.transition = 'background-color 1s';
    }

    // Unavailable state
    if (mainButton && state === 'unavailable') {
        mainButton.classList.add('is-unavailable');
    } else if (mainButton) {
        mainButton.classList.remove('is-unavailable');
    }

    // No CSS string needed
    return '';
})()}`
