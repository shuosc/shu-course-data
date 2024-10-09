import axios from 'axios';
import { logChain, moduleLog } from './logger';

export default function CreateClient(baseURL: string, moduleName: string) {
  const client = axios.create({
    baseURL,
  });
  const cookies: string[] = [];
  client.interceptors.request.use((config) => {
    if (cookies.length) {
      config.headers['Cookie'] = cookies.join('; ');
    }
    moduleLog(
      moduleName,
      logChain(
        config.method?.toUpperCase(),
        config.url,
        // config.headers['Cookie']
      )
    );
    return config;
  });
  client.interceptors.response.use((res) => {
    if (res.headers['set-cookie']) {
      res.headers['set-cookie']!.forEach((cookie) => {
        cookies.push(cookie);
      });
    }
    return res;
  });
  return client;
}
