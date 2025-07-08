`${(() => {
    const occupancy = hass?.states[this.config?.main_button_floors?.occupancy_entity]?.state || '';
    const hot = hass?.states[this.config?.main_button_floors?.hot_entity]?.state || '';
    const cold = hass?.states[this.config?.main_button_floors?.cold_entity]?.state || '';

    let bg_color = 'var(--bubble-main-background-color)';
    let occupied_color = 'var(--accent-color)';
    let hot_color = 'var(--error-color)';
    let cold_color = 'var(--purple-color)';

    // Main button background
    const mainButton = card?.querySelector('.bubble-button-background');
    if (mainButton) {
        mainButton.style.opacity = '1';
        mainButton.style.backgroundColor = occupancy === 'on' ? occupied_color : bg_color;
        mainButton.style.transition = 'background-color 1s';
    }

    // Sub button 1
    const subButton1 = card?.querySelector('.bubble-sub-button-1');
    if (subButton1) {
        if (hot === 'on') {
            subButton1.style.backgroundColor = hot_color;
        } else if (cold === 'on') {
            subButton1.style.backgroundColor = cold_color;
        } else if (occupancy === 'on') {
            subButton1.style.backgroundColor = occupied_color;
        } else {
            subButton1.style.backgroundColor = bg_color;
        }
    }

    // Unavailable state
    if (mainButton && occupancy === 'unavailable') {
        mainButton.classList.add('is-unavailable');
    } else if (mainButton) {
        mainButton.classList.remove('is-unavailable');
    }

    // No CSS string needed
    return '';
})()}`
