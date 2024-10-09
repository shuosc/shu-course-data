import chalk from 'chalk';

function getCurrentTime(less: boolean = false) {
  const date = new Date();
  return (
    `${date.getHours().toString().padStart(2, '0')}:${date
      .getMinutes()
      .toString()
      .padStart(2, '0')}` +
    (less
      ? ''
      : `:${date.getSeconds().toString().padStart(2, '0')}` +
        chalk.gray(`.${date.getMilliseconds().toString().padStart(3, '0')}`))
  );
}

export function log(...message: any[]) {
  console.log(getCurrentTime(), chalk.gray('>>'), ...message);
}

export function moduleLog(moduleName: string, ...message: any[]) {
  console.log(
    getCurrentTime(),
    chalk.gray('>>'),
    moduleName === 'OAUTH' ? chalk.blue(moduleName) : chalk.yellow(moduleName),
    chalk.gray('>>'),
    ...message
  );
}

export function logChain(...message: any[]) {
  return message.join(chalk.gray(' >> '));
}

export function messageLog(user: number | string, message: string) {
  console.log(
    chalk.yellow(`[${user}]`),
    chalk.gray(`${getCurrentTime(true)}`),
    message
  );
}

export const styles = {
  underline: chalk.underline,
};
