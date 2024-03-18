import { dispatchEvent } from "./events";
import { toast } from "./toast";

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
        container.appendChild(bookingElement);

        const { datetime } = bookingTarget.dataset;
        try {
            const data = await makeRequest(moveUrl, { to: datetime });
            toast('Saved: OK', 'success');
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
