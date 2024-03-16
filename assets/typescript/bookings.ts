import { dispatchEvent } from "./events";
import { toast } from "./toast";

declare global {
    interface Window {
        CSRFToken: string;
    }
}

export const moveBooking = async (bookingElement: HTMLElement, bookingTarget: HTMLElement): Promise<object> => {
    const container = bookingTarget.querySelector('.booking-group') || bookingTarget;
    const parent = bookingElement.parentElement;

    const { moveUrl } = bookingElement.dataset;
    if (moveUrl) {
        container.appendChild(bookingElement);
        const response = await fetch(moveUrl, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': window.CSRFToken },
            body: JSON.stringify({ to: bookingTarget.dataset.time })
        });
        const data = await response.json();
        if (!response.ok || !data) {
            const message = data.detail || response.statusText;
            parent && parent.appendChild(bookingElement);
            toast(`Error: ${message}`, "error");

            if (response.status !== 400) {
                throw new Error(message);
            }
        } else {
            toast('Saved: OK', 'success');
        }

        return data;
    } else {
        throw new Error("Move URL is not provided.");
    }
}
