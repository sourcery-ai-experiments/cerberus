import { dispatchEvent } from "./events";
import { toast } from "./toast";

declare global {
    interface Window {
        CSRFToken: string;
    }
}

export const moveBooking = (bookingElement: HTMLElement, bookingTarget: HTMLElement) => {
    return new Promise((resolve, _reject) => {
        const container = bookingTarget.querySelector('.booking-group') || bookingTarget;
        const parent = bookingElement.parentElement;
        container.appendChild(bookingElement);

        const reject = (reason: string) => {
            toast(reason, "error");
            _reject(reason);
        }

        const { moveUrl } = bookingElement.dataset;
        if (moveUrl) {
            fetch(moveUrl, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': window.CSRFToken },
                body: JSON.stringify({ to: bookingTarget.dataset.time })
            })
                .then((response) => response.ok ? response : Promise.reject(response))
                .then((response) => response.json())
                .then((data) => resolve(data))
                .catch((error) => {
                    parent && parent.appendChild(bookingElement);
                    if (error.status !== 400) {
                        reject(`Error: ${error.statusText}`);
                    } else {
                        error.json().then((data) => reject(`Error: ${data.detail}`));
                    }
                });
        }
    });
}
