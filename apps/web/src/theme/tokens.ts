export const colorGroups = {
  'Nền': ['canvas', 'panel', 'raised', 'input'],
  'Đường viền': ['border', 'borderStrong'],
  'Chữ': ['text', 'secondary', 'muted'],
  'Tương tác': ['accent', 'focus', 'hover', 'selection', 'selectionText'],
  'Ý nghĩa': ['positive', 'negative', 'warning', 'info'],
  'Biểu đồ': ['series1', 'series2', 'series3', 'series4'],
} as const;
export type ColorRole = typeof colorGroups[keyof typeof colorGroups][number];
export type Colors = Record<ColorRole, string>;
export const colorLabels: Record<ColorRole, string> = {
  canvas:'Nền ứng dụng', panel:'Panel', raised:'Header / dialog', input:'Ô nhập',
  border:'Viền thường', borderStrong:'Viền nhấn', text:'Chữ chính', secondary:'Chữ phụ', muted:'Chú thích',
  accent:'Màu nhấn', focus:'Focus bàn phím', hover:'Hover', selection:'Nền lựa chọn', selectionText:'Chữ lựa chọn',
  positive:'Tăng / tích cực', negative:'Giảm / lỗi', warning:'Cảnh báo', info:'Thông tin',
  series1:'Series 1', series2:'Series 2', series3:'Series 3', series4:'Series 4',
};
export const terminalColors: Colors = {
  canvas:'#000000', panel:'#0B0B0B', raised:'#151515', input:'#101010', border:'#2C2C2C', borderStrong:'#555555',
  text:'#EEEEEE', secondary:'#B8B8B8', muted:'#929292', accent:'#4DB5FF', focus:'#8BD0FF', hover:'#202020',
  selection:'#383838', selectionText:'#FFFFFF', positive:'#00D17B', negative:'#FF4D4F', warning:'#FFD000', info:'#4DB5FF',
  series1:'#E6E6E6', series2:'#4DB5FF', series3:'#FFD000', series4:'#B99AFF',
};
export const presets = {
  terminal: {name:'Terminal Black', colors:terminalColors},
  graphite: {name:'Graphite', colors:{...terminalColors,canvas:'#101010',panel:'#171717',raised:'#222222',input:'#1B1B1B',hover:'#292929',selection:'#404040'}},
  midnight: {name:'Midnight', colors:{...terminalColors,canvas:'#080C12',panel:'#0E141D',raised:'#182231',input:'#101925',border:'#2B3747',hover:'#1C2939',selection:'#304158'}},
} satisfies Record<string,{name:string;colors:Colors}>;
export type Preset = keyof typeof presets;
export const fontFamilies = {plex:'"IBM Plex Mono", monospace',jetbrains:'"JetBrains Mono", monospace'};
export function contrast(a:string,b:string):number {
  const luminance=(hex:string)=>{const rgb=[1,3,5].map(i=>parseInt(hex.slice(i,i+2),16)/255).map(v=>v<=.04045?v/12.92:((v+.055)/1.055)**2.4);return rgb[0]*.2126+rgb[1]*.7152+rgb[2]*.0722};
  const x=luminance(a),y=luminance(b);return (Math.max(x,y)+.05)/(Math.min(x,y)+.05);
}
