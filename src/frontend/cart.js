/**
 * Módulo de Gestión del Carrito Interactivo en Web Storage (AD-003, DTO-CART-001).
 * Implementa de forma determinista y reactiva las invariantes del dominio:
 * - INV-002: Cantidades enteras >= 1. Eliminación automática si cantidad < 1.
 * - INV-004: Consistencia aritmética estricta (subtotal = unit_price * quantity, total_amount = sum(subtotals)).
 * Cero persistencia en servidor y cero dependencias externas.
 */

export class CartManager {
  /**
   * @param {string} storageKey - Clave en localStorage (default: 'shopping_cart')
   */
  constructor(storageKey = 'shopping_cart') {
    this.storageKey = storageKey;
    this.listeners = [];
  }

  /**
   * Suscribe un listener que se ejecuta cuando el estado del carrito cambia.
   * @param {Function} listener - Callback (state) => void
   * @returns {Function} Función para cancelar la suscripción
   */
  subscribe(listener) {
    if (typeof listener === 'function') {
      this.listeners.push(listener);
    }
    return () => {
      this.listeners = this.listeners.filter(l => l !== listener);
    };
  }

  /**
   * Notifica a todos los suscriptores el estado actual.
   * @private
   */
  _notify(state) {
    for (const listener of this.listeners) {
      try {
        listener(state);
      } catch (err) {
        console.error('Error al notificar suscriptor de carrito:', err);
      }
    }
  }

  /**
   * Redondea un número a 2 decimales para garantizar consistencia aritmética (INV-004).
   * @param {number} val
   * @returns {number}
   */
  _round2(val) {
    return Math.round((val + Number.EPSILON) * 100) / 100;
  }

  /**
   * Recalcula los totales e invariantes del carrito a partir de la lista de ítems (INV-002, INV-004).
   * @private
   * @param {Array} rawItems
   * @returns {{items: Array, total_items: number, total_amount: number}}
   */
  _calculateState(rawItems) {
    const validItems = [];
    let totalItems = 0;
    let totalAmount = 0.0;

    for (const item of rawItems) {
      const qty = parseInt(item.quantity, 10);
      // INV-002: Solo se conservan ítems con cantidad >= 1
      if (!isNaN(qty) && qty >= 1) {
        const unitPrice = typeof item.unit_price === 'number' ? item.unit_price : parseFloat(item.unit_price) || 0.0;
        const subtotal = this._round2(unitPrice * qty);
        
        validItems.push({
          product_id: item.product_id,
          name: String(item.name || ''),
          unit_price: unitPrice,
          quantity: qty,
          subtotal: subtotal
        });

        totalItems += qty;
        totalAmount = this._round2(totalAmount + subtotal);
      }
    }

    return {
      items: validItems,
      total_items: totalItems,
      total_amount: this._round2(totalAmount)
    };
  }

  /**
   * Obtiene el estado actual del carrito desde localStorage o retorna el estado vacío.
   * @returns {{items: Array, total_items: number, total_amount: number}}
   */
  getState() {
    if (typeof window === 'undefined' || !window.localStorage) {
      return { items: [], total_items: 0, total_amount: 0.0 };
    }

    try {
      const raw = window.localStorage.getItem(this.storageKey);
      if (!raw) {
        return { items: [], total_items: 0, total_amount: 0.0 };
      }
      const parsed = JSON.parse(raw);
      if (!parsed || !Array.isArray(parsed.items)) {
        return { items: [], total_items: 0, total_amount: 0.0 };
      }
      return this._calculateState(parsed.items);
    } catch {
      return { items: [], total_items: 0, total_amount: 0.0 };
    }
  }

  /**
   * Guarda el estado en localStorage y notifica a los suscriptores.
   * @private
   * @param {{items: Array, total_items: number, total_amount: number}} state
   */
  _saveState(state) {
    if (typeof window !== 'undefined' && window.localStorage) {
      try {
        window.localStorage.setItem(this.storageKey, JSON.stringify(state));
      } catch (err) {
        console.error('Error al persistir carrito en localStorage:', err);
      }
    }
    this._notify(state);
    return state;
  }

  /**
   * Agrega un producto al carrito o incrementa su cantidad si ya existe (REQ-003, AC-004).
   * @param {{id: number, name: string, price: number}} product
   * @param {number} quantity - Cantidad a agregar (default: 1)
   * @returns {{items: Array, total_items: number, total_amount: number}}
   */
  addItem(product, quantity = 1) {
    if (!product || product.id === undefined || product.id === null) {
      return this.getState();
    }

    const qtyToAdd = Math.max(1, parseInt(quantity, 10) || 1);
    const currentState = this.getState();
    const existingIndex = currentState.items.findIndex(i => i.product_id === product.id);

    let updatedItems = [...currentState.items];
    if (existingIndex >= 0) {
      const existing = updatedItems[existingIndex];
      const newQty = existing.quantity + qtyToAdd;
      updatedItems[existingIndex] = {
        ...existing,
        quantity: newQty
      };
    } else {
      const unitPrice = typeof product.price === 'number' ? product.price : parseFloat(product.price) || 0.0;
      updatedItems.push({
        product_id: product.id,
        name: product.name,
        unit_price: unitPrice,
        quantity: qtyToAdd
      });
    }

    const newState = this._calculateState(updatedItems);
    return this._saveState(newState);
  }

  /**
   * Modifica la cantidad de un producto sumando el delta especificado (+1 o -1).
   * Si la cantidad resultante es menor a 1, el producto se elimina automáticamente (INV-002, AC-005).
   * @param {number} productId - Identificador del producto
   * @param {number} delta - Variación de cantidad (+1 o -1)
   * @returns {{items: Array, total_items: number, total_amount: number}}
   */
  updateQuantity(productId, delta) {
    const currentState = this.getState();
    const existingIndex = currentState.items.findIndex(i => i.product_id === productId);

    if (existingIndex < 0) {
      return currentState;
    }

    const existing = currentState.items[existingIndex];
    const newQty = existing.quantity + delta;

    let updatedItems;
    if (newQty < 1) {
      // INV-002: Si la cantidad cae por debajo de 1, se remueve automáticamente
      updatedItems = currentState.items.filter(i => i.product_id !== productId);
    } else {
      updatedItems = [...currentState.items];
      updatedItems[existingIndex] = {
        ...existing,
        quantity: newQty
      };
    }

    const newState = this._calculateState(updatedItems);
    return this._saveState(newState);
  }

  /**
   * Elimina un producto del carrito por su identificador único (AC-005).
   * @param {number} productId
   * @returns {{items: Array, total_items: number, total_amount: number}}
   */
  removeItem(productId) {
    const currentState = this.getState();
    const updatedItems = currentState.items.filter(i => i.product_id !== productId);
    const newState = this._calculateState(updatedItems);
    return this._saveState(newState);
  }

  /**
   * Vacía completamente el carrito de compras (AC-006).
   * @returns {{items: Array, total_items: number, total_amount: number}}
   */
  clearCart() {
    const emptyState = { items: [], total_items: 0, total_amount: 0.0 };
    return this._saveState(emptyState);
  }
}

// Instancia singleton por defecto para la aplicación
export const cartInstance = new CartManager();
