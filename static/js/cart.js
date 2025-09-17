// static/js/cart.js

document.addEventListener('DOMContentLoaded', () => {
    // --- 1. CORE CART LOGIC ---
    const getCart = () => JSON.parse(localStorage.getItem('cart')) || [];
    const saveCart = (cart) => {
        localStorage.setItem('cart', JSON.stringify(cart));
        updateCartDisplay();
    };

    const addToCart = (item) => {
        const cart = getCart();
        const existingItem = cart.find(cartItem => cartItem.id === item.id);
        if (existingItem) {
            existingItem.quantity++;
        } else {
            cart.push({ ...item, quantity: 1 });
        }
        saveCart(cart);
    };

    const updateQuantity = (itemId, change) => {
        let cart = getCart();
        const item = cart.find(cartItem => cartItem.id === itemId);
        if (item) {
            item.quantity += change;
            if (item.quantity <= 0) {
                cart = cart.filter(cartItem => cartItem.id !== itemId);
            }
        }
        saveCart(cart);
    };

    // --- 2. DOM ELEMENTS & UI UPDATES ---
    const cartModal = document.getElementById('cart-modal');
    const cartItemsContainer = document.getElementById('cart-items');
    const cartTotalEl = document.getElementById('cart-total');
    const orderItemsInput = document.getElementById('order-items');
    
    const updateCartDisplay = () => {
        const cart = getCart();
        cartItemsContainer.innerHTML = '';
        let total = 0;

        if (cart.length === 0) {
            cartItemsContainer.innerHTML = '<p class="text-center text-gray-500">Your cart is empty.</p>';
        } else {
            cart.forEach(item => {
                total += item.price * item.quantity;
                const itemDiv = document.createElement('div');
                itemDiv.className = 'flex items-center gap-4 py-3 border-b';
                itemDiv.innerHTML = `
                    <div class="flex-1">
                        <p class="font-semibold text-gray-800">${item.name}</p>
                        <p class="text-sm text-rose-600">₹${item.price.toFixed(2)}</p>
                    </div>
                    <div class="flex items-center gap-2">
                        <button class="quantity-btn" data-id="${item.id}" data-change="-1">-</button>
                        <span class="font-bold w-8 text-center">${item.quantity}</span>
                        <button class="quantity-btn" data-id="${item.id}" data-change="1">+</button>
                    </div>
                `;
                cartItemsContainer.appendChild(itemDiv);
            });
        }
        
        cartTotalEl.textContent = `₹${total.toFixed(2)}`;
        const orderPayload = cart.map(item => ({ item_id: item.id, quantity: item.quantity }));
        orderItemsInput.value = JSON.stringify(orderPayload);
        updateCartCountBadges(cart);
    };
    
    const updateCartCountBadges = (cart) => {
        const totalItems = cart.reduce((sum, item) => sum + item.quantity, 0);
        document.querySelectorAll('.cart-count').forEach(el => {
            el.textContent = totalItems;
        });
    };
    
    // --- 3. EVENT LISTENERS ---
    document.body.addEventListener('click', e => {
        // Add to Cart buttons on the menu page
        if (e.target.closest('.add-to-cart-btn')) {
            const button = e.target.closest('.add-to-cart-btn');
            const item = {
                id: button.dataset.id,
                name: button.dataset.name,
                price: parseFloat(button.dataset.price)
            };
            addToCart(item);
        }

        // View Cart buttons in both navbars
        if (e.target.closest('.view-cart-btn')) {
            updateCartDisplay();
            cartModal.classList.remove('hidden');
        }

        // Close cart button
        if (e.target.closest('#close-cart-btn')) {
            cartModal.classList.add('hidden');
        }
        
        // Quantity buttons inside modal
        if (e.target.classList.contains('quantity-btn')) {
            const id = e.target.dataset.id;
            const change = parseInt(e.target.dataset.change, 10);
            updateQuantity(id, change);
        }
    });

    // Close modal if clicking on the background overlay
    if (cartModal) {
        cartModal.addEventListener('click', e => {
            if (e.target === cartModal) {
                cartModal.classList.add('hidden');
            }
        });
    }

    // --- 4. INITIALIZATION ---
    updateCartCountBadges(getCart());
});