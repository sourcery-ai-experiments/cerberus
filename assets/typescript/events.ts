export const dispatchEvent = (element: HTMLElement, eventName: string, detail: any) => {
    element.dispatchEvent(new CustomEvent(eventName, { bubbles: true, detail }));
}
