import { moveBooking } from './bookings';
import { toast } from './toast';

declare global {
    interface Window {
        moveBooking: typeof moveBooking;
        toast: typeof toast;
    }
}

window.moveBooking = moveBooking;
window.toast = toast;
