        // Cart
        let cart = JSON.parse(localStorage.getItem('skyyrose_cart')) || [];
        
        function updateCartCount() {
            document.getElementById('cartCount').textContent = cart.reduce((sum, item) => sum + item.qty, 0);
        }
        updateCartCount();

        // Quantity
        let qty = 1;
        document.getElementById('qtyMinus').addEventListener('click', () => {
            if (qty > 1) {
                qty--;
                document.getElementById('qtyValue').textContent = qty;
            }
        });
        document.getElementById('qtyPlus').addEventListener('click', () => {
            qty++;
            document.getElementById('qtyValue').textContent = qty;
        });

        // Size selection
        document.querySelectorAll('.size-btn:not(.disabled)').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.size-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
            });
        });

        // Color selection
        document.querySelectorAll('.color-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.color-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                document.getElementById('colorName').textContent = btn.dataset.color;
            });
        });

        // Add to cart
        document.getElementById('addToCart').addEventListener('click', () => {
            const size = document.querySelector('.size-btn.active')?.textContent || 'M';
            const color = document.getElementById('colorName').textContent;
            
            const item = {
                id: 'thorn-hoodie-' + size + '-' + color,
                name: 'Thorn Hoodie',
                collection: 'Black Rose',
                price: 185,
                size: size,
                color: color,
                qty: qty
            };

            const existingIndex = cart.findIndex(i => i.id === item.id);
            if (existingIndex > -1) {
                cart[existingIndex].qty += qty;
            } else {
                cart.push(item);
            }

            localStorage.setItem('skyyrose_cart', JSON.stringify(cart));
            updateCartCount();

            // Show toast
            const toast = document.getElementById('toast');
            toast.classList.add('show');
            setTimeout(() => toast.classList.remove('show'), 3000);
        });

        // Accordions
        document.querySelectorAll('.accordion-header').forEach(header => {
            header.addEventListener('click', () => {
                const item = header.parentElement;
                item.classList.toggle('open');
            });
        });

        // Thumbnail selection
        document.querySelectorAll('.thumbnail').forEach((thumb, index) => {
            thumb.addEventListener('click', () => {
                document.querySelectorAll('.thumbnail').forEach(t => t.classList.remove('active'));
                thumb.classList.add('active');
            });
        });
