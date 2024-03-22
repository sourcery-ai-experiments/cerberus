const className = 'toast-container';

const Document = document;

const createContainer = (): HTMLElement => {
    const container = Document.createElement('div');
    container.className = className;
    Document.body.appendChild(container);
    return container;
}

const getContainer = (): HTMLElement => {
    return Document.querySelector(`.${className}`) || createContainer();
}

export type ToastType = "success" | "error" | "warn" | "info";

export const toast = (message: string, type: ToastType = "info", duration: number = 3000) => {
    const container = getContainer();
    const toast = Document.createElement('div');
    toast.classList.add('toast', type);
    toast.innerHTML = message;
    container.appendChild(toast);

    toast.addEventListener('click', () => toast.classList.add('remove'));
    toast.addEventListener("animationend", (event) => {
        switch (event.animationName) {
            case 'remove':
                container.removeChild(toast);
                break;
            case 'add':
                setTimeout(() => toast.classList.add('remove'), duration);
                break;
        }
    });
}
