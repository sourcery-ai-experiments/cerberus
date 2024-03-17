import { moveBooking, moveBookingDay } from './bookings';
import { toast } from './toast';

declare global {
    interface Window {
        moveBooking: typeof moveBooking;
        moveBookingDay: typeof moveBookingDay;
        toast: typeof toast;
    }
}

window.moveBooking = moveBooking;
window.moveBookingDay = moveBookingDay;
window.toast = toast;
