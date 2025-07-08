${(() => {
    const occupancy = hass?.states[this.config?.main_button_outdoors?.occupancy_entity]?.state || '';

    let bg_color = 'var(--bubble-main-background-color)';
    let occupied_color = 'var(--accent-color)';

    // Main button background
    const mainButton = card?.querySelector('.bubble-button-background');
    if (mainButton) {
        mainButton.style.opacity = '1';
        mainButton.style.backgroundColor = occupancy === 'on' ? occupied_color : bg_color;
        mainButton.style.transition = 'background-color 1s';
    }

    // Unavailable state
    if (mainButton && occupancy === 'unavailable') {
        mainButton.classList.add('is-unavailable');
    } else if (mainButton) {
        mainButton.classList.remove('is-unavailable');
    }

    // No CSS string needed
    return '';
})()}
