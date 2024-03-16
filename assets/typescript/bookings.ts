import { dispatchEvent } from "./events";
import { toast } from "./toast";

declare global {
    interface Window {
        CSRFToken: string;
    }
}

export const moveBooking = (bookingElement: HTMLElement, bookingTarget: HTMLElement) => {
    const container = bookingTarget.querySelector('.booking-group') || bookingTarget;
    const parent = bookingElement.parentElement;
    container.appendChild(bookingElement);

    const { moveUrl } = bookingElement.dataset;
    if (moveUrl) {
        fetch(moveUrl, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': window.CSRFToken },
            body: JSON.stringify({ to: bookingTarget.dataset.time })
        })
            .then((r) => r.ok ? r : Promise.reject(r))
            .then(() => dispatchEvent(bookingTarget, 'booking-move', { id: bookingElement.dataset.id }))
            .catch((err) => {
                parent && parent.appendChild(bookingElement);
                if (err.status !== 400) {
                    toast(`Error: ${err.statusText}`, 'error');
                } else {
                    err.json().then((data) => toast(`Error: ${data.detail}`, 'error'));
                }
            });
    }
}
