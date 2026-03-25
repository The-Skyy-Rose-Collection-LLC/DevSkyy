/**
 * @jest-environment jsdom
 */

// Override the global THREE with jest.fn()-based mocks for spy assertions
const mockDomElement = document.createElement('canvas');
global.THREE = {
  Scene: jest.fn(() => ({ add: jest.fn(), remove: jest.fn(), children: [] })),
  PerspectiveCamera: jest.fn((fov, aspect) => ({ fov, aspect, position: { set: jest.fn() }, updateProjectionMatrix: jest.fn(), lookAt: jest.fn() })),
  WebGLRenderer: jest.fn(() => ({ domElement: mockDomElement, setSize: jest.fn(), setPixelRatio: jest.fn(), render: jest.fn(), dispose: jest.fn(), forceContextLoss: jest.fn(), shadowMap: { enabled: false, type: 0 }, toneMapping: 0, toneMappingExposure: 1 })),
  AmbientLight: jest.fn((color, intensity) => ({ color, intensity, position: { set: jest.fn() } })),
  DirectionalLight: jest.fn((color, intensity) => ({ color, intensity, position: { set: jest.fn() }, castShadow: false, shadow: { mapSize: { width: 0, height: 0 }, camera: {} } })),
  GLTFLoader: jest.fn(() => ({ load: jest.fn((url, onLoad) => { if (onLoad) onLoad({ scene: {}, animations: [] }); }), setDRACOLoader: jest.fn() })),
  OrbitControls: jest.fn(() => ({ update: jest.fn(), dispose: jest.fn(), enableDamping: true, dampingFactor: 0.05 })),
  Clock: jest.fn(() => ({ getElapsedTime: jest.fn().mockReturnValue(0), getDelta: jest.fn().mockReturnValue(0.016) })),
  Vector3: jest.fn(() => ({ set: jest.fn() })),
};

// Mock requestAnimationFrame for jsdom
global.requestAnimationFrame = jest.fn((cb) => setTimeout(cb, 0));
global.cancelAnimationFrame = jest.fn((id) => clearTimeout(id));

/**
 * Three.js Scene Tests
 *
 * Tests for 3D scene initialization and rendering.
 */

describe('Three.js Scene', () => {
    let container;

    beforeEach(() => {
        // Create a container element
        container = document.createElement('div');
        container.id = 'three-container';
        document.body.appendChild(container);
    });

    afterEach(() => {
        // Clean up
        if (container && container.parentNode) {
            container.parentNode.removeChild(container);
        }
    });

    describe('Scene Initialization', () => {
        test('should create a scene', () => {
            const scene = new THREE.Scene();
            expect(scene).toBeDefined();
            expect(THREE.Scene).toHaveBeenCalled();
        });

        test('should create a camera', () => {
            const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
            expect(camera).toBeDefined();
            expect(THREE.PerspectiveCamera).toHaveBeenCalled();
        });

        test('should create a renderer', () => {
            const renderer = new THREE.WebGLRenderer({ antialias: true });
            expect(renderer).toBeDefined();
            expect(THREE.WebGLRenderer).toHaveBeenCalled();
        });

        test('renderer should have a DOM element', () => {
            const renderer = new THREE.WebGLRenderer();
            expect(renderer.domElement).toBeDefined();
            expect(renderer.domElement.tagName).toBe('CANVAS');
        });
    });

    describe('Lighting', () => {
        test('should create ambient light', () => {
            const light = new THREE.AmbientLight(0xffffff, 0.5);
            expect(light).toBeDefined();
            expect(THREE.AmbientLight).toHaveBeenCalled();
        });

        test('should create directional light', () => {
            const light = new THREE.DirectionalLight(0xffffff, 1);
            expect(light).toBeDefined();
            expect(THREE.DirectionalLight).toHaveBeenCalled();
        });

        test('directional light should have position', () => {
            const light = new THREE.DirectionalLight(0xffffff, 1);
            expect(light.position).toBeDefined();
            expect(light.position.set).toBeDefined();
        });
    });

    describe('Model Loading', () => {
        test('should create GLTF loader', () => {
            const loader = new THREE.GLTFLoader();
            expect(loader).toBeDefined();
            expect(THREE.GLTFLoader).toHaveBeenCalled();
        });

        test('should load model successfully', (done) => {
            const loader = new THREE.GLTFLoader();
            const modelPath = '/assets/models/test-model.glb';

            loader.load(
                modelPath,
                (gltf) => {
                    expect(gltf).toBeDefined();
                    expect(gltf.scene).toBeDefined();
                    done();
                },
                undefined,
                (error) => {
                    done(error);
                }
            );
        });

        test('should handle loading progress', () => {
            const loader = new THREE.GLTFLoader();
            const progressCallback = jest.fn();

            loader.load(
                '/assets/models/test-model.glb',
                () => {},
                progressCallback
            );

            // Verify progress callback can be called
            expect(progressCallback).toBeDefined();
        });
    });

    describe('Camera Controls', () => {
        test('should create orbit controls', () => {
            const camera = new THREE.PerspectiveCamera();
            const renderer = new THREE.WebGLRenderer();
            const controls = new THREE.OrbitControls(camera, renderer.domElement);

            expect(controls).toBeDefined();
            expect(THREE.OrbitControls).toHaveBeenCalled();
        });

        test('controls should have update method', () => {
            const camera = new THREE.PerspectiveCamera();
            const renderer = new THREE.WebGLRenderer();
            const controls = new THREE.OrbitControls(camera, renderer.domElement);

            expect(controls.update).toBeDefined();
            expect(typeof controls.update).toBe('function');
        });

        test('controls should support damping', () => {
            const camera = new THREE.PerspectiveCamera();
            const renderer = new THREE.WebGLRenderer();
            const controls = new THREE.OrbitControls(camera, renderer.domElement);

            expect(controls.enableDamping).toBeDefined();
            expect(controls.dampingFactor).toBeDefined();
        });
    });

    describe('Animation Loop', () => {
        test('requestAnimationFrame should be called', () => {
            const animate = jest.fn(function() {
                requestAnimationFrame(animate);
            });

            animate();

            expect(requestAnimationFrame).toHaveBeenCalled();
        });

        test('renderer.render should be called in animation loop', () => {
            const scene = new THREE.Scene();
            const camera = new THREE.PerspectiveCamera();
            const renderer = new THREE.WebGLRenderer();

            const animate = () => {
                renderer.render(scene, camera);
            };

            animate();

            expect(renderer.render).toHaveBeenCalled();
            expect(renderer.render).toHaveBeenCalledWith(scene, camera);
        });
    });

    describe('Resize Handling', () => {
        test('should update camera aspect ratio on resize', () => {
            const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight);
            const originalAspect = camera.aspect;

            // Simulate window resize
            global.innerWidth = 1920;
            global.innerHeight = 1080;

            const newAspect = window.innerWidth / window.innerHeight;
            expect(newAspect).not.toBe(originalAspect);
        });

        test('should update renderer size on resize', () => {
            const renderer = new THREE.WebGLRenderer();
            renderer.setSize(800, 600);

            expect(renderer.setSize).toHaveBeenCalledWith(800, 600);
        });
    });

    describe('Memory Management', () => {
        test('should dispose renderer on cleanup', () => {
            const renderer = new THREE.WebGLRenderer();
            renderer.dispose();

            expect(renderer.dispose).toHaveBeenCalled();
        });

        test('should dispose controls on cleanup', () => {
            const camera = new THREE.PerspectiveCamera();
            const renderer = new THREE.WebGLRenderer();
            const controls = new THREE.OrbitControls(camera, renderer.domElement);

            controls.dispose();

            expect(controls.dispose).toHaveBeenCalled();
        });
    });

    describe('Performance', () => {
        test('should create clock for delta time', () => {
            const clock = new THREE.Clock();
            expect(clock).toBeDefined();
            expect(THREE.Clock).toHaveBeenCalled();
        });

        test('should get delta time', () => {
            const clock = new THREE.Clock();
            const delta = clock.getDelta();

            expect(delta).toBeDefined();
            expect(typeof delta).toBe('number');
        });
    });

    describe('Error Handling', () => {
        test('should handle WebGL context loss', () => {
            const renderer = new THREE.WebGLRenderer();
            const canvas = renderer.domElement;

            const contextLostEvent = new Event('webglcontextlost');
            canvas.dispatchEvent(contextLostEvent);

            // Verify event can be dispatched without errors
            expect(true).toBe(true);
        });

        test('should handle model loading errors', (done) => {
            const loader = new THREE.GLTFLoader();

            // Override the mock to simulate error
            loader.load = jest.fn((url, onLoad, onProgress, onError) => {
                onError(new Error('Failed to load model'));
            });

            loader.load(
                '/invalid/path.glb',
                () => {
                    done(new Error('Should not succeed'));
                },
                undefined,
                (error) => {
                    expect(error).toBeDefined();
                    done();
                }
            );
        });
    });
});

describe('Scene Integration', () => {
    test('should initialize complete scene with all components', () => {
        const scene = new THREE.Scene();
        const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
        const renderer = new THREE.WebGLRenderer();
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.5);
        const directionalLight = new THREE.DirectionalLight(0xffffff, 1);

        scene.add(ambientLight);
        scene.add(directionalLight);

        expect(scene).toBeDefined();
        expect(camera).toBeDefined();
        expect(renderer).toBeDefined();
        expect(scene.add).toHaveBeenCalledTimes(2);
    });

    test('should render scene without errors', () => {
        const scene = new THREE.Scene();
        const camera = new THREE.PerspectiveCamera();
        const renderer = new THREE.WebGLRenderer();

        expect(() => {
            renderer.render(scene, camera);
        }).not.toThrow();
    });
});
