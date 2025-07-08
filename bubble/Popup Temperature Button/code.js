`${(() => {
    const hot = hass?.states[this.config?.popup_temperature_button?.hot_entity]?.state || '';
    const cold = hass?.states[this.config?.popup_temperature_button?.cold_entity]?.state || '';

    let bg_color = 'var(--background-color-2)';
    let hot_color = 'var(--error-color)';
    let cold_color = 'var(--cyan-color)';

    // Main button background
    const mainButton = card?.querySelector('.bubble-button-background');
    if (mainButton) {
        mainButton.style.opacity = '1';
        if (hot === 'on') {
            mainButton.style.backgroundColor = hot_color;
        } else if (cold === 'on') {
            mainButton.style.backgroundColor = cold_color;
        } else {
            mainButton.style.backgroundColor = bg_color;
        }
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
