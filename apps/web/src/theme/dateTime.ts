import type {DateTimeRegion} from './preferences';

const formats = {
  vietnam: {locale:'vi-VN',timeZone:'Asia/Ho_Chi_Minh',zoneLabel:'ICT'},
  'united-states': {locale:'en-US',timeZone:'America/New_York',zoneLabel:'ET'},
} as const;

export function formatDate(value:string|number|Date,region:DateTimeRegion){
  const {locale,timeZone}=formats[region];
  return new Intl.DateTimeFormat(locale,{day:'2-digit',month:'2-digit',year:'numeric',timeZone}).format(new Date(value));
}

export function formatDateTime(value:string|number|Date,region:DateTimeRegion){
  const {locale,timeZone,zoneLabel}=formats[region];
  return `${new Intl.DateTimeFormat(locale,{day:'2-digit',month:'2-digit',year:'numeric',hour:'2-digit',minute:'2-digit',hour12:region==='united-states',timeZone}).format(new Date(value))} ${zoneLabel}`;
}
