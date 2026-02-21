import * as THREE from 'three';

/**
 * Rolling Sphere Controller with Movement Platforms and Air Jumps
 * Based on Catlike Coding principles
 * Features: Velocity Inheritance and Triple Jump mechanics
 */
export class RollingSphere {
    
    constructor(radius = 0.5) {
        this.radius = radius;
        this.physicsEnabled = true;
        
        // Physics properties
        this.velocity = new THREE.Vector3();
        this.desiredVelocity = new THREE.Vector3();
        
        // Use CustomGravity system instead of fixed gravity
        this.customGravity = null; // Will be set by external system
        this.isGrounded = false;
        this.groundNormal = new THREE.Vector3(0, 1, 0);
        this.contactNormal = new THREE.Vector3();
        this.activeNormal = new THREE.Vector3(0, 1, 0); // Normal of the active surface
        this.avgNormal = new THREE.Vector3(0, 1, 0); // Average normal for planar calculations
        
        // Jump properties
        this.jumpCount = 0;
        this.jumpPhase = 0;
        this.jumpImpulse = 0; // Will be calculated dynamically
        this.maxJumpCount = 3;
        
        // Moving platform interaction
        this.connectionVelocity = new THREE.Vector3();
        this.connectedBody = null;
        
        // Movement parameters
        this.maxSpeed = 5;
        this.maxAcceleration = 10;
        this.maxAirAcceleration = 5;
        this.alignmentSpeed = 5;
        
        // Physics damping - set to 0 for high-speed falling
        this.linearDamping = 0; // Set to 0 to remove air resistance
        
        // Sphere representation
        this.sphere = new THREE.Mesh(
            new THREE.SphereGeometry(radius, 32, 32),
            new THREE.MeshStandardMaterial({ color: 0x00ff00 })
        );
        this.sphere.position.y = radius;
        
        // Collision settings
        this.groundLayer = 1;
        
        // Temporary vectors for calculations
        this._tempVector = new THREE.Vector3();
        this._tempVector2 = new THREE.Vector3();
        this._tempVector3 = new THREE.Vector3();
    }
    
    /**
     * Set custom gravity system reference
     * @param {Object} customGravity - CustomGravity instance
     */
    setCustomGravity(customGravity) {
        this.customGravity = customGravity;
        this.calculateJumpImpulse();
    }
    
    /**
     * Calculate required jump impulse for specific height based on current gravity
     * @param {number} targetHeight - Desired jump height (6.0 units)
     */
    calculateJumpImpulse(targetHeight = 6.0) {
        if (!this.customGravity) {
            // Fallback to fixed gravity
            const gravityMagnitude = 15; // Default gravity magnitude
            this.jumpImpulse = Math.sqrt(2 * gravityMagnitude * targetHeight);
            return;
        }
        
        // Get gravity magnitude at current position
        const gravity = this.customGravity.getGravity(this.sphere.position);
        const gravityMagnitude = gravity.length();
        
        // Use formula: v = sqrt(2 * magnitude * h) 
        // This ensures exactly 6.0 units height
        this.jumpImpulse = Math.sqrt(2 * gravityMagnitude * targetHeight);
    }
    
    /**
     * Update method called each frame
     * @param {number} deltaTime - Time since last frame
     * @param {Object} input - User input object
     */
    update(deltaTime, input) {
        if (!this.physicsEnabled) return;
        
        // Store previous state
        const previousGrounded = this.isGrounded;
        
        // Clear movement state
        this.isGrounded = false;
        this.connectedBody = null;
        this.connectionVelocity.set(0, 0, 0);
        this.activeNormal.set(0, 1, 0); // Reset to default
        this.avgNormal.set(0, 1, 0); // Reset avgNormal
        
        // Handle collisions and ground detection
        this.updateCollisions();
        
        // Update desired velocity based on input
        this.updateDesiredVelocity(input);
        
        // Apply movement physics
        this.updateVelocity(deltaTime);
        
        // Apply gravity if not grounded
        if (!this.isGrounded) {
            const gravity = this.getCurrentGravity();
            this.velocity.addScaledVector(gravity, deltaTime);
        }
        
        // Handle jumping
        this.updateJumpState(input, deltaTime, previousGrounded);
        
        // Move the sphere
        this.moveSphere(deltaTime);
        
        // Apply linear damping to horizontal movement only (not vertical)
        this.applyDamping(deltaTime);
        
        // Update sphere rotation based on movement
        this.updateRotation(deltaTime);
    }
    
    /**
     * Get current gravity vector
     * @returns {THREE.Vector3}
     */
    getCurrentGravity() {
        if (this.customGravity && this.customGravity.getGravity) {
            return this.customGravity.getGravity(this.sphere.position);
        }
        // Fallback gravity
        return new THREE.Vector3(0, -15, 0);
    }
    
    /**
     * Update collision detection and handle moving platform interactions
     */
    updateCollisions() {
        // This would typically involve raycasting or physics engine integration
        // For now, we'll implement a basic ground detection
        
        const groundRay = new THREE.Raycaster(
            this.sphere.position,
            new THREE.Vector3(0, -1, 0),
            0,
            this.radius + 0.1
        );
        
        // This is where you would check for collisions with moving platforms
        // For demonstration, we'll assume ground detection at y = 0
        const groundY = 0;
        if (this.sphere.position.y - this.radius <= groundY + 0.1) {
            this.isGrounded = true;
            this.groundNormal.set(0, 1, 0);
            this.activeNormal.copy(this.groundNormal); // Set active normal
            this.avgNormal.copy(this.groundNormal); // Set avgNormal for planar calculations
            this.sphere.position.y = groundY + this.radius;
            
            // Reset jump count when grounded
            this.jumpCount = 0;
            
            // If connected to moving platform, inherit velocity
            if (this.connectedBody) {
                // Calculate connection velocity based on platform movement
                this.connectionVelocity.copy(this.connectedBody.velocity);
            }
        }
        
        // Dynamically recalculate jump impulse based on current gravity
        this.calculateJumpImpulse();
    }
    
    /**
     * Update desired velocity based on player input
     * @param {Object} input - Input state
     */
    updateDesiredVelocity(input) {
        this.desiredVelocity.set(0, 0, 0);
        
        // Apply input direction (assuming WASD-style input)
        if (input.moveForward) this.desiredVelocity.z -= 1;
        if (input.moveBackward) this.desiredVelocity.z += 1;
        if (input.moveLeft) this.desiredVelocity.x -= 1;
        if (input.moveRight) this.desiredVelocity.x += 1;
        
        // Normalize and scale to max speed
        if (this.desiredVelocity.lengthSq() > 1) {
            this.desiredVelocity.normalize();
        }
        this.desiredVelocity.multiplyScalar(this.maxSpeed);
        
        // Add connection velocity for moving platforms
        this.desiredVelocity.add(this.connectionVelocity);
    }
    
    /**
     * Update velocity based on desired movement and physics
     * @param {number} deltaTime
     */
    updateVelocity(deltaTime) {
        const currentAcceleration = this.isGrounded ? 
            this.maxAcceleration : this.maxAirAcceleration;
        
        // Step 1: Calculate targetVelocity as (moveDir * maxSpeed) + (connectionVelocity projected on ground plane)
        const targetVelocity = this._tempVector.copy(this.desiredVelocity);
        
        // If there's platform velocity, ensure it's properly projected onto the tangent plane
        if (!this.connectionVelocity.equals(new THREE.Vector3(0, 0, 0))) {
            const platformVelPlanar = this._tempVector2.copy(this.connectionVelocity);
            const normalDotPlatform = platformVelPlanar.dot(this.avgNormal);
            platformVelPlanar.addScaledVector(this.avgNormal, -normalDotPlatform);
            targetVelocity.add(platformVelPlanar);
        }
        
        // Step 2: Calculate currentPlanarVelocity by projecting this.velocity onto the avgNormal tangent plane
        const currentPlanarVelocity = this._tempVector2.copy(this.velocity);
        const normalDotCurrent = currentPlanarVelocity.dot(this.avgNormal);
        currentPlanarVelocity.addScaledVector(this.avgNormal, -normalDotCurrent);
        
        // Step 3: Calculate velocity diff = (targetVelocity - currentPlanarVelocity)
        const diff = this._tempVector3;
        diff.subVectors(targetVelocity, currentPlanarVelocity);
        
        // Step 4: Clamp diff magnitude by (maxAcceleration * dt)
        const maxVelocityChange = currentAcceleration * deltaTime;
        if (diff.lengthSq() > maxVelocityChange * maxVelocityChange) {
            diff.normalize().multiplyScalar(maxVelocityChange);
        }
        
        // Step 5: Apply diff back to this.body.velocity
        // This ensures only planar components are modified, vertical gravity untouched
        this.velocity.add(diff);
    }
    
    /**
     * Apply linear damping to horizontal movement only (preserve vertical gravity)
     * @param {number} deltaTime
     */
    applyDamping(deltaTime) {
        if (this.linearDamping > 0) {
            // Apply damping only to horizontal components
            const horizontalVelocity = new THREE.Vector3(this.velocity.x, 0, this.velocity.z);
            const dampingFactor = 1 - this.linearDamping * deltaTime;
            horizontalVelocity.multiplyScalar(dampingFactor);
            
            // Recombine with vertical velocity
            this.velocity.x = horizontalVelocity.x;
            this.velocity.z = horizontalVelocity.z;
        }
    }
    
    /**
     * Handle jumping mechanics
     * @param {Object} input - Input state
     * @param {number} deltaTime
     * @param {boolean} previousGrounded
     */
    updateJumpState(input, deltaTime, previousGrounded) {
        // Jump request handling
        if (input.jumpPressed) {
            // Handle jump queuing
            if (this.isGrounded && this.jumpPhase === 0) {
                this.jumpPhase = 1;
            } else if (!previousGrounded && this.isGrounded) {
                this.jumpPhase = 2;
            }
        }
        
        // Execute jump
        if (this.jumpPhase > 0) {
            if (this.canJump()) {
                this.executeJump();
            }
            this.jumpPhase = 0;
        }
    }
    
    /**
     * Check if jump is allowed based on triple jump logic
     * @returns {boolean}
     */
    canJump() {
        // Allow jump if grounded or jump count is less than max
        return this.isGrounded || this.jumpCount < this.maxJumpCount;
    }
    
    /**
     * Execute the jump with calibrated impulse
     */
    executeJump() {
        // Apply the calculated jump impulse directly
        this.velocity.y = this.jumpImpulse;
        this.velocity.addScaledVector(this.contactNormal, this.jumpImpulse * 0.1); // Small forward boost
        this.isGrounded = false;
        this.jumpCount++;
    }
    
    /**
     * Move the sphere based on current velocity
     * @param {number} deltaTime
     */
    moveSphere(deltaTime) {
        this.sphere.position.addScaledVector(this.velocity, deltaTime);
    }
    
    /**
     * Rotate sphere based on movement direction
     * @param {number} deltaTime
     */
    updateRotation(deltaTime) {
        // Calculate rotation based on horizontal movement
        const horizontalVelocity = new THREE.Vector3(
            this.velocity.x,
            0,
            this.velocity.z
        );
        
        if (horizontalVelocity.lengthSq() > 0.01) {
            // Create rotation quaternion towards movement direction
            const targetRotation = new THREE.Quaternion();
            const upVector = new THREE.Vector3(0, 1, 0);
            targetRotation.setFromUnitVectors(
                new THREE.Vector3(0, 0, 1),
                horizontalVelocity.clone().normalize()
            );
            
            // Smoothly interpolate rotation
            this.sphere.quaternion.slerp(targetRotation, this.alignmentSpeed * deltaTime);
        }
    }
    
    /**
     * Set connection to moving platform
     * @param {Object} platform - Platform object with velocity
     * @param {THREE.Vector3} contactNormal - Normal at contact point
     */
    setPlatformConnection(platform, contactNormal) {
        this.connectedBody = platform;
        this.contactNormal.copy(contactNormal);
        this.activeNormal.copy(contactNormal); // Set the active normal for planar calculations
        this.avgNormal.copy(contactNormal); // Set avgNormal for planar calculations
        this.isGrounded = true;
        this.jumpCount = 0; // Reset jump count on platform contact
    }
    
    /**
     * Clear platform connection
     */
    clearPlatformConnection() {
        this.connectedBody = null;
        this.isGrounded = false;
        this.activeNormal.set(0, 1, 0); // Reset to default
        this.avgNormal.set(0, 1, 0); // Reset avgNormal
    }
    
    /**
     * Get sphere mesh for Three.js scene
     * @returns {THREE.Mesh}
     */
    getMesh() {
        return this.sphere;
    }
    
    /**
     * Get current position
     * @returns {THREE.Vector3}
     */
    getPosition() {
        return this.sphere.position.clone();
    }
    
    /**
     * Set position
     * @param {THREE.Vector3} position
     */
    setPosition(position) {
        this.sphere.position.copy(position);
    }
    
    /**
     * Get current velocity
     * @returns {THREE.Vector3}
     */
    getVelocity() {
        return this.velocity.clone();
    }
    
    /**
     * Reset sphere to initial state
     */
    reset() {
        this.sphere.position.set(0, this.radius, 0);
        this.velocity.set(0, 0, 0);
        this.jumpCount = 0;
        this.jumpPhase = 0;
        this.isGrounded = false;
        this.connectedBody = null;
        this.connectionVelocity.set(0, 0, 0);
        this.activeNormal.set(0, 1, 0);
        this.avgNormal.set(0, 1, 0);
    }
}

/**
 * Example Moving Platform class
 */
export class MovingPlatform {
    constructor(width = 2, height = 0.5, depth = 2) {
        this.mesh = new THREE.Mesh(
            new THREE.BoxGeometry(width, height, depth),
            new THREE.MeshStandardMaterial({ color: 0x8888ff })
        );
        this.velocity = new THREE.Vector3();
        this.movementBounds = new THREE.Box3();
        this.speed = 2;
    }
    
    update(deltaTime) {
        // Simple back-and-forth movement
        this.mesh.position.addScaledVector(this.velocity, deltaTime);
        
        // Update platform velocity (example movement pattern)
        // This would be overridden by more complex movement logic
        if (Math.abs(this.mesh.position.x) > 5) {
            this.velocity.x *= -1;
        }
    }
    
    getVelocity() {
        return this.velocity.clone();
    }
}