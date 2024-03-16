const className = 'toast-container';

const createContainer = (): HTMLElement => {
    const container = document.createElement('div');
    container.className = className;
    document.body.appendChild(container);
    return container;
}

const getContainer = (): HTMLElement => {
    return document.querySelector(`.${className}`) || createContainer();
}

export type ToastType = "success" | "error" | "warn" | "info";

export const toast = (message: string, type: ToastType = "info", duration: number = 3000) => {
    const container = getContainer();
    const toast = document.createElement('div');
    toast.classList.add('toast', type);
    toast.innerHTML = message;
    container.appendChild(toast);
    setTimeout(() => container.removeChild(toast), duration);
}
