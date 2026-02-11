        let cart = JSON.parse(localStorage.getItem('skyyrose_cart')) || [];
        document.getElementById('cartCount').textContent = cart.length;
