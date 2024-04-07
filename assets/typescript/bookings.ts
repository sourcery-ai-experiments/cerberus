import { toast } from "./toast";
import { dispatchEvent } from "./events";

declare global {
    interface Window {
        CSRFToken: string;
    }
}

const makeRequest = async (url: string, body: object): Promise<object> => {
    const response = await fetch(url, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': window.CSRFToken },
        body: JSON.stringify(body)
    });
    const data = await response.json();
    if (!response.ok || !data) {
        const message = data.detail || response.statusText;
        throw new Error(message);
    }

    return data;
}

export const moveBooking = async (bookingElement: HTMLElement, bookingTarget: HTMLElement, containerSelector: string): Promise<object> => {
    const container = bookingTarget.querySelector(containerSelector) || bookingTarget;
    const parent = bookingElement.parentElement;

    const { moveUrl } = bookingElement.dataset;
    if (moveUrl) {
        if (bookingElement.matches(containerSelector) && container.matches(containerSelector)) {
            Array.from(bookingElement.children).forEach(element => container.appendChild(element));
            bookingElement.remove();
        } else {
            container.appendChild(bookingElement);
        }

        const { datetime } = bookingTarget.dataset;
        try {
            const data = await makeRequest(moveUrl, { to: datetime });
            toast('Saved: OK', 'success');
            dispatchEvent(bookingElement, 'booking-moved', data);
            return data;
        } catch (error) {
            parent && parent.appendChild(bookingElement);
            toast(`${error}`, "error");
            return {};
        }
    } else {
        throw new Error("Move URL is not provided.");
    }
}
