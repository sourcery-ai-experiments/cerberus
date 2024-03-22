const mathRound = Math.round

export const roundTime = (datetime: string, roundTo: number = 15): string => {
    const rounded = new Date(datetime);

    rounded.setMilliseconds(mathRound(rounded.getMilliseconds() / 1000) * 1000);
    rounded.setSeconds(mathRound(rounded.getSeconds() / 60) * 60);
    rounded.setMinutes(mathRound(rounded.getMinutes() / roundTo) * roundTo);

    return rounded.toISOString().slice(0,-8);
}
