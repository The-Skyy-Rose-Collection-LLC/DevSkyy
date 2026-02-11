        let cart = JSON.parse(localStorage.getItem('skyyrose_cart')) || [];
        let shippingCost = 15;

        function renderOrderItems() {
            const container = document.getElementById('orderItems');
            
            if (cart.length === 0) {
                window.location.href = 'cart.html';
                return;
            }

            container.innerHTML = cart.map(item => `
                <div class="order-item">
                    <div class="order-item-image">
                        <span class="order-item-qty">${item.qty}</span>
                    </div>
                    <div class="order-item-details">
                        <h4>${item.name}</h4>
                        <p>${item.size} / ${item.color}</p>
                    </div>
                    <span class="order-item-price">$${(item.price * item.qty).toFixed(0)}</span>
                </div>
            `).join('');

            updateTotals();
        }

        function updateTotals() {
            const subtotal = cart.reduce((sum, item) => sum + (item.price * item.qty), 0);
            
            // Free shipping over $150
            if (subtotal >= 150) {
                shippingCost = 0;
                document.getElementById('standardPrice').textContent = 'FREE';
            }
            
            const tax = subtotal * 0.0875; // ~8.75% tax
            const total = subtotal + shippingCost + tax;

            document.getElementById('subtotal').textContent = `$${subtotal.toFixed(0)}`;
            document.getElementById('shippingCost').textContent = shippingCost === 0 ? 'FREE' : `$${shippingCost}`;
            document.getElementById('tax').textContent = `$${tax.toFixed(2)}`;
            document.getElementById('total').textContent = `$${total.toFixed(2)}`;
        }

        // Shipping method selection
        document.querySelectorAll('.shipping-option').forEach(option => {
            option.addEventListener('click', () => {
                document.querySelectorAll('.shipping-option').forEach(o => o.classList.remove('selected'));
                option.classList.add('selected');
                option.querySelector('input').checked = true;

                const value = option.querySelector('input').value;
                const subtotal = cart.reduce((sum, item) => sum + (item.price * item.qty), 0);
                
                if (subtotal >= 150 && value === 'standard') {
                    shippingCost = 0;
                } else if (value === 'standard') {
                    shippingCost = 15;
                } else if (value === 'express') {
                    shippingCost = 25;
                } else if (value === 'overnight') {
                    shippingCost = 45;
                }
                
                updateTotals();
            });
        });

        // Form submission
        document.getElementById('checkoutForm').addEventListener('submit', (e) => {
            e.preventDefault();
            
            // Generate order number
            const orderNum = 'SR-2025-' + Math.random().toString(36).substr(2, 6).toUpperCase();
            document.getElementById('orderNumber').textContent = orderNum;
            
            // Clear cart
            localStorage.removeItem('skyyrose_cart');
            
            // Show success modal
            document.getElementById('successModal').classList.add('show');
        });

        // Initialize
        renderOrderItems();
