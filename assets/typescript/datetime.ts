import { round } from './alias';
import { pad } from './utils';

export const pad2 = (n: number): string => pad(n, 2);

export const dateToString = (date: Date|string): string => {
    const d = typeof date === 'string' ? new Date(date) : date;
    return `${d.getFullYear()}-${pad2(d.getMonth()+1)}-${pad2(d.getDate())}T${pad2(d.getHours())}:${pad2(d.getMinutes())}`
}

export const roundTime = (datetime: Date|string, roundTo: number = 15): string => {
    const rounded = new Date(datetime);

    rounded.setMilliseconds(round(rounded.getMilliseconds() / 1000) * 1000);
    rounded.setSeconds(round(rounded.getSeconds() / 60) * 60);
    rounded.setMinutes(round(rounded.getMinutes() / roundTo) * roundTo);

    return dateToString(rounded);
}

export const addMinutes = (date: Date|string, minutes: number): Date => {
    return new Date(new Date(date).getTime() + minutes*60000);
}
