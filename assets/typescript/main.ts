import { moveBooking } from './bookings';
import { toast } from './toast';
import { roundTime, addMinutes, dateToString } from './datetime';

declare global {
    interface Window {
        moveBooking: typeof moveBooking;
        toast: typeof toast;
        roundTime: typeof roundTime;
        addMinutes: typeof addMinutes;
        dateToString: typeof dateToString;
    }
}

const Window = window;

Window.moveBooking = moveBooking;
Window.toast = toast;
Window.roundTime = roundTime;
Window.addMinutes = addMinutes;
Window.dateToString = dateToString;
