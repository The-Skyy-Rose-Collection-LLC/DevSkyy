/**
 * Jest Setup File
 *
 * Global setup for all test files.
 */

// Mock Three.js
global.THREE = {
    WebGLRenderer: jest.fn().mockImplementation(() => ({
        setSize: jest.fn(),
        setPixelRatio: jest.fn(),
        render: jest.fn(),
        dispose: jest.fn(),
        domElement: document.createElement('canvas')
    })),
    Scene: jest.fn().mockImplementation(() => ({
        add: jest.fn(),
        remove: jest.fn()
    })),
    PerspectiveCamera: jest.fn().mockImplementation(() => ({
        position: { set: jest.fn(), x: 0, y: 0, z: 5 },
        lookAt: jest.fn()
    })),
    AmbientLight: jest.fn(),
    DirectionalLight: jest.fn().mockImplementation(() => ({
        position: { set: jest.fn() },
        castShadow: false
    })),
    GLTFLoader: jest.fn().mockImplementation(() => ({
        load: jest.fn((url, onLoad, onProgress, onError) => {
            onLoad({ scene: {} });
        })
    })),
    OrbitControls: jest.fn().mockImplementation(() => ({
        update: jest.fn(),
        dispose: jest.fn(),
        enableDamping: true,
        dampingFactor: 0.05
    })),
    Vector3: jest.fn().mockImplementation((x, y, z) => ({ x, y, z })),
    Color: jest.fn(),
    Clock: jest.fn().mockImplementation(() => ({
        getDelta: jest.fn(() => 0.016)
    }))
};

// Mock window.requestAnimationFrame
global.requestAnimationFrame = jest.fn((callback) => {
    setTimeout(callback, 16);
    return 1;
});

global.cancelAnimationFrame = jest.fn();

// Mock window.matchMedia
Object.defineProperty(window, 'matchMedia', {
    writable: true,
    value: jest.fn().mockImplementation(query => ({
        matches: false,
        media: query,
        onchange: null,
        addListener: jest.fn(),
        removeListener: jest.fn(),
        addEventListener: jest.fn(),
        removeEventListener: jest.fn(),
        dispatchEvent: jest.fn(),
    })),
});

// Mock ResizeObserver
global.ResizeObserver = jest.fn().mockImplementation(() => ({
    observe: jest.fn(),
    unobserve: jest.fn(),
    disconnect: jest.fn(),
}));

// Mock IntersectionObserver
global.IntersectionObserver = jest.fn().mockImplementation(() => ({
    observe: jest.fn(),
    unobserve: jest.fn(),
    disconnect: jest.fn(),
}));

// Mock console methods to reduce noise in tests
global.console = {
    ...console,
    error: jest.fn(),
    warn: jest.fn(),
    log: jest.fn(),
};

// Mock WordPress global objects
global.wp = {
    ajax: {
        post: jest.fn(),
        send: jest.fn()
    }
};

global.skyyRoseData = {
    ajaxUrl: '/wp-admin/admin-ajax.php',
    nonce: 'test-nonce',
    themeUri: '/wp-content/themes/skyyrose-flagship',
    assetsUri: '/wp-content/themes/skyyrose-flagship/assets',
    modelsPath: '/wp-content/themes/skyyrose-flagship/assets/models/'
};

// jQuery mock
global.$ = global.jQuery = jest.fn((selector) => {
    const element = document.querySelector(selector);
    return {
        length: element ? 1 : 0,
        on: jest.fn(),
        off: jest.fn(),
        trigger: jest.fn(),
        addClass: jest.fn(),
        removeClass: jest.fn(),
        toggleClass: jest.fn(),
        hasClass: jest.fn(),
        find: jest.fn(),
        attr: jest.fn(),
        data: jest.fn(),
        val: jest.fn(),
        hide: jest.fn(),
        show: jest.fn(),
        fadeIn: jest.fn(),
        fadeOut: jest.fn(),
        0: element
    };
});
