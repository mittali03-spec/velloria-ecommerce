// ========================================
// VELLORIA CART SYSTEM
// ========================================

// Keep the existing Velloria cart in localStorage
let cart = [];

try {
    cart = JSON.parse(localStorage.getItem("velloriaCart")) || [];

    if (!Array.isArray(cart)) {
        cart = [];
    }
} catch (error) {
    console.error("Could not read cart:", error);
    cart = [];
}


// ========================================
// SAVE CART
// ========================================

function saveCart() {

    localStorage.setItem(
        "velloriaCart",
        JSON.stringify(cart)
    );

    updateCartCount();
}


// ========================================
// UPDATE CART COUNT
// ========================================

function updateCartCount() {

    const cartCount =
        document.getElementById("cart-count");

    if (!cartCount) {
        return;
    }

    let totalQuantity = 0;

    cart.forEach(function(item) {

        totalQuantity +=
            Number(item.quantity) || 0;

    });

    cartCount.textContent = totalQuantity;
}


// ========================================
// ADD PRODUCT TO CART
// ========================================

function addToCart(name, price, image) {

    price = Number(price);

    if (!name || isNaN(price)) {

        alert("Unable to add this product to cart.");

        return;
    }


    const existingItem = cart.find(function(item) {

        return item.name === name;

    });


    if (existingItem) {

        existingItem.quantity =
            Number(existingItem.quantity) + 1;

        // If an image was supplied later,
        // save it to the existing product.
        if (image && !existingItem.image) {
            existingItem.image = image;
        }

    } else {

        cart.push({

            name: name,

            price: price,

            image: image || "",

            quantity: 1

        });

    }


    saveCart();

    // Refresh cart if we are currently on cart page
    displayCart();

    alert(
    "🛒 Your product has been added to cart!"
);
}


// ========================================
// DISPLAY CART
// ========================================

function displayCart() {

    const cartContainer =
        document.getElementById("cart-items");

    if (!cartContainer) {
        return;
    }


    const emptyCart =
        document.getElementById("empty-cart");

    const cartLayout =
        document.getElementById("cart-layout");


    // ====================================
    // EMPTY CART
    // ====================================

    if (cart.length === 0) {

        cartContainer.innerHTML = "";

        if (emptyCart) {
            emptyCart.style.display = "flex";
        }

        if (cartLayout) {
            cartLayout.style.display = "none";
        }

        updateCartSummary();

        return;
    }


    // ====================================
    // CART HAS PRODUCTS
    // ====================================

    if (emptyCart) {
        emptyCart.style.display = "none";
    }

    if (cartLayout) {
        cartLayout.style.display = "grid";
    }


    cartContainer.innerHTML = "";


    cart.forEach(function(item, index) {

        const price =
            Number(item.price) || 0;

        const quantity =
            Number(item.quantity) || 1;

        const itemTotal =
            price * quantity;


        const cartItem =
            document.createElement("div");

        cartItem.className = "cart-item";


        // Product image
        let imageHTML = "";

        if (item.image) {

            imageHTML = `
                <img
                    src="${item.image}"
                    alt="${escapeHTML(item.name)}"
                    class="cart-product-image"
                    onerror="this.style.display='none'"
                >
            `;

        } else {

            imageHTML = `
                <div class="cart-product-placeholder">
                    🛍️
                </div>
            `;

        }


        cartItem.innerHTML = `

            <div class="cart-product">

                ${imageHTML}

                <div class="cart-product-info">

                    <h3>
                        ${escapeHTML(item.name)}
                    </h3>

                    <p>
                        ₹${price.toFixed(2)}
                    </p>

                </div>

            </div>


            <div class="quantity-controls">

                <button
                    type="button"
                    onclick="decreaseQuantity(${index})">

                    −

                </button>


                <span>
                    ${quantity}
                </span>


                <button
                    type="button"
                    onclick="increaseQuantity(${index})">

                    +

                </button>

            </div>


            <div class="item-total">

                ₹${itemTotal.toFixed(2)}

            </div>


            <button
                type="button"
                class="remove-button"
                onclick="removeFromCart(${index})">

                Remove

            </button>

        `;


        cartContainer.appendChild(cartItem);

    });


    updateCartSummary();
}


// ========================================
// ESCAPE HTML
// ========================================

function escapeHTML(value) {

    return String(value)

        .replace(/&/g, "&amp;")

        .replace(/</g, "&lt;")

        .replace(/>/g, "&gt;")

        .replace(/"/g, "&quot;")

        .replace(/'/g, "&#039;");
}


// ========================================
// INCREASE QUANTITY
// ========================================

function increaseQuantity(index) {

    if (!cart[index]) {
        return;
    }


    cart[index].quantity =
        Number(cart[index].quantity) + 1;


    saveCart();

    displayCart();
}


// ========================================
// DECREASE QUANTITY
// ========================================

function decreaseQuantity(index) {

    if (!cart[index]) {
        return;
    }


    const quantity =
        Number(cart[index].quantity);


    if (quantity > 1) {

        cart[index].quantity =
            quantity - 1;

    } else {

        cart.splice(index, 1);

    }


    saveCart();

    displayCart();
}


// ========================================
// REMOVE PRODUCT
// ========================================

function removeFromCart(index) {

    if (!cart[index]) {
        return;
    }


    const productName =
        cart[index].name;


    cart.splice(index, 1);


    saveCart();

    displayCart();


    if (productName) {

        console.log(
            productName + " removed from cart."
        );

    }
}


// ========================================
// CALCULATE CART TOTAL
// ========================================

function calculateCartTotal() {

    let total = 0;


    cart.forEach(function(item) {

        const price =
            Number(item.price) || 0;

        const quantity =
            Number(item.quantity) || 0;


        total +=
            price * quantity;

    });


    return total;
}


// ========================================
// UPDATE CART SUMMARY
// ========================================

function updateCartSummary() {

    const total =
        calculateCartTotal();


    const subtotalElement =
        document.getElementById(
            "cart-subtotal"
        );


    const totalElement =
        document.getElementById(
            "cart-total"
        );


    if (subtotalElement) {

        subtotalElement.textContent =
            "₹" + total.toFixed(2);

    }


    if (totalElement) {

        totalElement.textContent =
            "₹" + total.toFixed(2);

    }


    // Update number of products
    const itemLabel =
        document.getElementById(
            "cart-item-label"
        );


    if (itemLabel) {

        let totalQuantity = 0;


        cart.forEach(function(item) {

            totalQuantity +=
                Number(item.quantity) || 0;

        });


        if (totalQuantity === 1) {

            itemLabel.textContent =
                "1 item";

        } else {

            itemLabel.textContent =
                totalQuantity + " items";

        }

    }
}


// ========================================
// OLD FUNCTION NAME
// ========================================

function updateTotal() {

    updateCartSummary();

}


// ========================================
// CHECKOUT BUTTON
// ========================================

async function checkout() {

    if (cart.length === 0) {

        alert(
            "Your cart is empty. Please add a product first."
        );

        return;
    }


    try {

        const response =
            await fetch("/api/session");


        if (!response.ok) {

            throw new Error(
                "Could not check login status."
            );

        }


        const data =
            await response.json();


        if (!data.logged_in) {

            showLoginRequiredPopup();

            return;
        }


        window.location.href =
            "/checkout";


    } catch (error) {

        console.error(
            "Checkout error:",
            error
        );


        alert(
            "Something went wrong. Please try again."
        );

    }
}


// ========================================
// LOGIN REQUIRED POPUP
// ========================================

function showLoginRequiredPopup() {

    const oldPopup =
        document.getElementById(
            "login-required-popup"
        );


    if (oldPopup) {

        oldPopup.remove();

    }


    const popup =
        document.createElement("div");


    popup.id =
        "login-required-popup";


    popup.innerHTML = `

        <div class="login-popup-overlay">

            <div class="login-popup">

                <button
                    type="button"
                    class="popup-close"
                    onclick="closeLoginPopup()">

                    ×

                </button>


                <div class="popup-icon">
                    🛒
                </div>


                <h2>
                    Login Required
                </h2>


                <p>
                    Please login or sign in
                    before proceeding to buy.
                </p>


                <div class="popup-buttons">

                    <button
                        type="button"
                        class="popup-cancel"
                        onclick="closeLoginPopup()">

                        Cancel

                    </button>


                    <button
                        type="button"
                        class="popup-login"
                        onclick="goToLogin()">

                        Login / Sign In

                    </button>

                </div>

            </div>

        </div>

    `;


    document.body.appendChild(popup);
}


// ========================================
// CLOSE LOGIN POPUP
// ========================================

function closeLoginPopup() {

    const popup =
        document.getElementById(
            "login-required-popup"
        );


    if (popup) {

        popup.remove();

    }
}


// ========================================
// GO TO LOGIN
// ========================================

function goToLogin() {

    window.location.href =
        "/login?next=checkout";
}


// ========================================
// PLACE ORDER
// ========================================

async function placeOrder() {

    if (cart.length === 0) {

        alert(
            "Your cart is empty."
        );

        return;
    }


    const button =
        document.getElementById(
            "place-order-button"
        );


    if (button) {

        button.disabled = true;

        button.textContent =
            "Placing Order...";

    }


    try {

        const response =
            await fetch(
                "/api/create-order",
                {

                    method: "POST",

                    headers: {

                        "Content-Type":
                            "application/json"

                    },

                    body: JSON.stringify({

                        items: cart

                    })

                }
            );


        const data =
            await response.json();


        // Login required
        if (response.status === 401) {

            window.location.href =
                "/login?next=checkout";

            return;
        }


        if (!data.ok) {

            alert(
                data.message ||
                "Could not place order."
            );

            return;
        }


        // =================================
        // ORDER SUCCESS
        // =================================

     // =================================
// ORDER SUCCESS
// =================================

cart = [];

saveCart();


alert(
    "Order placed successfully! 🎉\n\n" +
    "Order #" +
    data.customer_order_no
);


window.location.href =
    "/orders";
    
// ========================================
// PAGE LOAD
// ========================================

document.addEventListener(
    "DOMContentLoaded",
    function() {

        updateCartCount();

        displayCart();

    }
);