import { round } from './alias';


export const dateToString = (date: Date|string): string => {
    return (new Date(date)).toISOString().slice(0,-8);
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
