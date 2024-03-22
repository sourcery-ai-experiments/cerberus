import { moveBooking } from './bookings';
import { toast } from './toast';
import { roundTime } from './datetime';

declare global {
    interface Window {
        moveBooking: typeof moveBooking;
        toast: typeof toast;
        roundTime: typeof roundTime;
    }
}

const Window = window;

window.moveBooking = moveBooking;
window.toast = toast;
window.roundTime = roundTime;
