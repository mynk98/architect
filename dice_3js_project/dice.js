// dice.js
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
camera.position.z = 5;

const renderer = new THREE.WebGLRenderer();
renderer.setSize(window.innerWidth, window.innerHeight);
document.body.appendChild(renderer.domElement);

// Create materials for each face of the dice
const materials = [];
for (let i = 1; i <= 6; i++) {
    const canvas = document.createElement('canvas');
    canvas.width = 256;
canvas.height = 256;
    drawDiceFace(canvas, i);
    materials.push(new THREE.MeshBasicMaterial({ map: new THREE.CanvasTexture(canvas) }));
}

// Create the cube and apply materials to each face
const geometry = new THREE.BoxGeometry(2, 2, 2);
const dice = new THREE.Mesh(geometry, materials);
dice.rotation.y = Math.PI / 4;
scene.add(dice);

function drawDiceFace(canvas, dots) {
    const ctx = canvas.getContext('2d');
    ctx.fillStyle = 'white';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = 'black';
    if (dots === 1) {
drawDot(ctx, canvas.width / 2, canvas.height / 2);
} else if (dots === 2) {
drawDot(ctx, canvas.width / 4, canvas.height / 4);
drawDot(ctx, canvas.width * 3 / 4, canvas.height * 3 / 4);
} else if (dots === 3) {
drawDot(ctx, canvas.width / 4, canvas.height / 4);
drawDot(ctx, canvas.width / 2, canvas.height / 2);
drawDot(ctx, canvas.width * 3 / 4, canvas.height * 3 / 4);
} else if (dots === 4) {
drawDot(ctx, canvas.width / 4, canvas.height / 4);
drawDot(ctx, canvas.width * 3 / 4, canvas.height / 4);
drawDot(ctx, canvas.width / 4, canvas.height * 3 / 4);
drawDot(ctx, canvas.width * 3 / 4, canvas.height * 3 / 4);
} else if (dots === 5) {
drawDot(ctx, canvas.width / 2, canvas.height / 2);
drawDot(ctx, canvas.width / 4, canvas.height / 4);
drawDot(ctx, canvas.width * 3 / 4, canvas.height / 4);
drawDot(ctx, canvas.width / 4, canvas.height * 3 / 4);
drawDot(ctx, canvas.width * 3 / 4, canvas.height * 3 / 4);
} else if (dots === 6) {
drawDot(ctx, canvas.width / 4, canvas.height / 4);
drawDot(ctx, canvas.width * 3 / 4, canvas.height / 4);
drawDot(ctx, canvas.width / 4, canvas.height / 2);
drawDot(ctx, canvas.width * 3 / 4, canvas.height / 2);
drawDot(ctx, canvas.width / 4, canvas.height * 3 / 4);
drawDot(ctx, canvas.width * 3 / 4, canvas.height * 3 / 4);
}
}

function drawDot(ctx, x, y) {
ctx.beginPath();
ctx.arc(x, y, 20, 0, Math.PI * 2);
ctx.fill();
}

function animate() {
requestAnimationFrame(animate);
dice.rotation.y += 0.01;
renderer.render(scene, camera);
}

window.addEventListener('click', () => {
    dice.rotation.y = Math.random() * Math.PI * 2;
});

animate();