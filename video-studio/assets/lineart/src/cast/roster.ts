// roster.ts — the locked cast. Change a character here only on purpose:
// the video studio treats these specs as final once approved.
import type { Spec } from './rig.ts';

export const ROSTER: Spec[] = [
  { id: 'bac-si-minh', name: 'Bác sĩ Minh', role: 'Bác sĩ', build: 'adult', sex: 'nam',
    top: 'coat', topColor: '#fdfdfc', sleeve: 'long', bottom: 'trousers', bottomColor: '#4a4f57',
    hair: 'side', extras: ['stethoscope', 'glasses'], prop: 'none' },
  { id: 'dieu-duong-lan', name: 'Điều dưỡng Lan', role: 'Điều dưỡng', build: 'adult', sex: 'nu', height: 0.95,
    top: 'scrubs', topColor: '#7fb3c6', sleeve: 'short', bottom: 'trousers', bottomColor: '#7fb3c6',
    hair: 'bun', hat: 'nurse', hatColor: '#fdfdfc', extras: ['mask'], prop: 'none', shoeColor: '#fdfdfc' },
  { id: 'can-bo-thu', name: 'Chị Thu', role: 'Cán bộ kiểm dịch y tế', build: 'adult', sex: 'nu', height: 0.95,
    top: 'shirt', topColor: '#c3d6e8', sleeve: 'long', bottom: 'trousers', bottomColor: '#2c3b52',
    hair: 'ponytail', hat: 'officer', hatColor: '#2c3b52', extras: ['lanyard'], prop: 'clipboard' },
  { id: 'co-giao-hoa', name: 'Cô Hoa', role: 'Giáo viên', build: 'adult', sex: 'nu', height: 0.95,
    top: 'aodai', topColor: '#7fa3c7', sleeve: 'long', bottom: 'plain', bottomColor: '#fdfdfc',
    hair: 'long', prop: 'books' },
  { id: 'chi-nam', name: 'Chị Năm', role: 'Bán hàng rong', build: 'adult', sex: 'nu', height: 0.94,
    top: 'baba', topColor: '#a9573f', sleeve: 'long', bottom: 'wide', bottomColor: '#2b2b2b',
    hair: 'bun', hat: 'nonla', hatColor: '#e9d7a3', prop: 'ganh', gait: { stride: 20, period: 0.86 } },
  { id: 'ba-sau', name: 'Bà Sáu', role: 'Người cao tuổi', build: 'elder', sex: 'nu', height: 0.9, stoop: 6,
    top: 'baba', topColor: '#6e5a86', sleeve: 'long', bottom: 'wide', bottomColor: '#2b2b2b',
    hair: 'bun', hairColor: '#b8b2a6', prop: 'basket' },
  { id: 'anh-tuan', name: 'Anh Tuấn', role: 'Công nhân', build: 'adult', sex: 'nam',
    top: 'shirt', topColor: '#5c7896', sleeve: 'long', bottom: 'trousers', bottomColor: '#39414d',
    hair: 'short', hat: 'hardhat', hatColor: '#e5b53a', extras: ['vest'], prop: 'none' },
  { id: 'anh-khoa', name: 'Anh Khoa', role: 'Hành khách', build: 'adult', sex: 'nam',
    top: 'jacket', topColor: '#5f7a66', sleeve: 'long', bottom: 'trousers', bottomColor: '#3d4f6b',
    hair: 'short', hat: 'cap', hatColor: '#2b2b2b', extras: ['mask'], prop: 'suitcase', propColor: '#2f5d6b' },
  { id: 'anh-duc', name: 'Anh Đức', role: 'Nhân viên văn phòng', build: 'adult', sex: 'nam',
    top: 'shirt', topColor: '#ece6d6', sleeve: 'long', bottom: 'trousers', bottomColor: '#2f3540',
    hair: 'side', extras: ['tie'], prop: 'briefcase' },
  { id: 'ong-bay', name: 'Ông Bảy', role: 'Người cao tuổi', build: 'elder', sex: 'nam', height: 0.97, stoop: 9,
    top: 'shirt', topColor: '#d8cfb5', sleeve: 'long', bottom: 'trousers', bottomColor: '#6b6455',
    hair: 'short', hairColor: '#c9c4ba', extras: ['glasses'], prop: 'cane' },
  { id: 'be-an', name: 'Bé An', role: 'Học sinh', build: 'child', sex: 'nam',
    top: 'shirt', topColor: '#fdfdfc', sleeve: 'short', bottom: 'shorts', bottomColor: '#2f4466',
    hair: 'short', extras: ['redscarf'], prop: 'backpack', propColor: '#3f6ea8' },
  { id: 'be-mai', name: 'Bé Mai', role: 'Em nhỏ', build: 'child', sex: 'nu',
    top: 'dress', topColor: '#d9826e', sleeve: 'short', bottom: 'plain', bottomColor: '#fdfdfc',
    hair: 'pigtails', prop: 'none', shoeColor: '#a33a2e' },
];

export const byId = (id: string): Spec => {
  const s = ROSTER.find((r) => r.id === id);
  if (!s) throw new Error(`unknown character ${id}`);
  return s;
};
