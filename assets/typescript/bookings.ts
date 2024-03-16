import { dispatchEvent } from "./events";
import { toast } from "./toast";

declare global {
    interface Window {
        CSRFToken: string;
    }
}

export const moveBooking = async (bookingElement: HTMLElement, bookingTarget: HTMLElement) => {
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
        if (!response.ok) {
            const message = response.status != 400 ? response.statusText : data.detail;
            parent && parent.appendChild(bookingElement);
            toast(`Error: ${message}`, "error");
            throw new Error(message);
        }

        toast('Updated', 'success');
        return data;
    } else {
        throw new Error("Error");
    }
}
