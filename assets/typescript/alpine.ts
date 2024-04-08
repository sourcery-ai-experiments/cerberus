import Alpine from 'alpinejs';

import collapse from '@alpinejs/collapse'
import focus from '@alpinejs/focus'
import mask from '@alpinejs/mask'

Alpine.plugin(collapse);
Alpine.plugin(focus);
Alpine.plugin(mask);

declare global {
    interface Window {
        Alpine: typeof Alpine;
    }
}

window.Alpine = Alpine;

Alpine.start();
