import { create } from 'zustand';
import type { CartItem, Item } from '../types';

interface CartState {
  items: CartItem[];
  addItem: (item: Item, quantity?: number) => void;
  removeItem: (itemId: number) => void;
  updateQuantity: (itemId: number, delta: number) => void;
  setQuantity: (itemId: number, quantity: number) => void;
  clearCart: () => void;
  getTotalItems: () => number;
  getTotalPrice: () => number;
}

export const useCartStore = create<CartState>((set, get) => ({
  items: [],

  addItem: (item: Item, quantity = 1) => {
    set((state) => {
      const existing = state.items.find((i) => i.id_item === item.id);
      if (existing) {
        return {
          items: state.items.map((i) =>
            i.id_item === item.id ? { ...i, quantidade: i.quantidade + quantity } : i
          ),
        };
      }
      return {
        items: [
          ...state.items,
          {
            id_item: item.id,
            nome: item.nome,
            quantidade: quantity,
            valor_unitario: Number(item.valor_venda),
          },
        ],
      };
    });
  },

  removeItem: (itemId: number) => {
    set((state) => ({
      items: state.items.filter((i) => i.id_item !== itemId),
    }));
  },

  updateQuantity: (itemId: number, delta: number) => {
    set((state) => {
      const updated = state.items
        .map((i) => {
          if (i.id_item === itemId) {
            const newQty = i.quantidade + delta;
            return newQty > 0 ? { ...i, quantidade: newQty } : null;
          }
          return i;
        })
        .filter(Boolean) as CartItem[];
      return { items: updated };
    });
  },

  setQuantity: (itemId: number, quantity: number) => {
    set((state) => {
      if (quantity <= 0) {
        return { items: state.items.filter((i) => i.id_item !== itemId) };
      }
      return {
        items: state.items.map((i) =>
          i.id_item === itemId ? { ...i, quantidade: quantity } : i
        ),
      };
    });
  },

  clearCart: () => set({ items: [] }),

  getTotalItems: () => {
    return get().items.reduce((acc, curr) => acc + curr.quantidade, 0);
  },

  getTotalPrice: () => {
    return get().items.reduce((acc, curr) => acc + curr.quantidade * curr.valor_unitario, 0);
  },
}));
