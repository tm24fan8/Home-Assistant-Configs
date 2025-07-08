`${(() => {
    let state;
    if (this.config?.state_color_button?.alt_entity) {
        state = hass?.states[this.config?.state_color_button?.alt_entity]?.state || '';
    } else {
        state = hass?.states[this.config?.entity]?.state || '';
    }

    let bg_color = 'var(--bubble-main-background-color)';
    
    // Use the configured color or default to accent color
    let on_color = this.config?.state_color_button?.color
        ? `var(--${this.config.state_color_button.color})`
        : 'var(--accent-color)';

    // Main button background
    const mainButton = card?.querySelector('.bubble-button-background');
    if (mainButton) {
        mainButton.style.opacity = '1';
        mainButton.style.backgroundColor = state === 'on' ? on_color : bg_color;
        mainButton.style.transition = 'background-color 1s';
    }

    // Unavailable state
    if (mainButton && state === 'unavailable') {
        mainButton.style.opacity = '0.5';
        mainButton.classList.add('is-unavailable');
    } else if (mainButton) {
        mainButton.classList.remove('is-unavailable');
    }

    // No CSS string needed
    return '';
})()}`
