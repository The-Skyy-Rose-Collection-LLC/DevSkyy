        let cart = JSON.parse(localStorage.getItem('skyyrose_cart')) || [];

        function updateCartCount() {
            document.getElementById('cartCount').textContent = cart.reduce((sum, item) => sum + item.qty, 0);
        }

        function renderCart() {
            const container = document.getElementById('cartItems');
            const itemCountEl = document.getElementById('itemCount');
            
            if (cart.length === 0) {
                container.innerHTML = `
                    <div class="empty-cart">
                        <div class="empty-cart-icon">🛒</div>
                        <h2>Your cart is empty</h2>
                        <p>Looks like you haven't added anything to your cart yet.</p>
                        <a href="homepage.html" class="btn btn-primary" style="display: inline-block; width: auto;">Start Shopping</a>
                    </div>
                `;
                document.getElementById('orderSummary').style.display = 'none';
                itemCountEl.textContent = '0 items';
                return;
            }

            document.getElementById('orderSummary').style.display = 'block';
            const totalItems = cart.reduce((sum, item) => sum + item.qty, 0);
            itemCountEl.textContent = `${totalItems} item${totalItems !== 1 ? 's' : ''}`;

            container.innerHTML = cart.map((item, index) => `
                <div class="cart-item" data-index="${index}">
                    <div class="cart-item-image"></div>
                    <div class="cart-item-details">
                        <span class="cart-item-collection">${item.collection}</span>
                        <h3 class="cart-item-name">${item.name}</h3>
                        <p class="cart-item-options">Size: ${item.size} / Color: ${item.color}</p>
                        <div class="cart-item-qty">
                            <button class="qty-btn" onclick="updateQty(${index}, -1)">−</button>
                            <span class="qty-value">${item.qty}</span>
                            <button class="qty-btn" onclick="updateQty(${index}, 1)">+</button>
                        </div>
                    </div>
                    <div class="cart-item-actions">
                        <span class="cart-item-price">$${(item.price * item.qty).toFixed(0)}</span>
                        <button class="cart-item-remove" onclick="removeItem(${index})">Remove</button>
                    </div>
                </div>
            `).join('');

            updateTotals();
        }

        function updateQty(index, change) {
            cart[index].qty = Math.max(1, cart[index].qty + change);
            localStorage.setItem('skyyrose_cart', JSON.stringify(cart));
            renderCart();
            updateCartCount();
        }

        function removeItem(index) {
            cart.splice(index, 1);
            localStorage.setItem('skyyrose_cart', JSON.stringify(cart));
            renderCart();
            updateCartCount();
        }

        function updateTotals() {
            const subtotal = cart.reduce((sum, item) => sum + (item.price * item.qty), 0);
            const shipping = subtotal >= 150 ? 0 : 15;
            const total = subtotal + shipping;

            document.getElementById('subtotal').textContent = `$${subtotal.toFixed(0)}`;
            document.getElementById('shipping').textContent = shipping === 0 ? 'FREE' : `$${shipping}`;
            document.getElementById('total').textContent = `$${total.toFixed(0)}`;
        }

        // Initialize
        renderCart();
        updateCartCount();

        // Demo: Add sample items if cart is empty (for testing)
        if (cart.length === 0) {
            // Uncomment to test with sample data
            /*
            cart = [
                { id: 'thorn-hoodie-M-black', name: 'Thorn Hoodie', collection: 'Black Rose', price: 185, size: 'M', color: 'Onyx Black', qty: 1 },
                { id: 'heartbreak-hoodie-L-rose', name: 'Heartbreak Hoodie', collection: 'Love Hurts', price: 195, size: 'L', color: 'Rose', qty: 2 }
            ];
            localStorage.setItem('skyyrose_cart', JSON.stringify(cart));
            renderCart();
            updateCartCount();
            */
        }
