export const pad = (n: number, len: number): string =>  n.toString().padStart(len, '0').slice(-len);
