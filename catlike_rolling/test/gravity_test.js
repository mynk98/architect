import * as THREE from 'three';
import { RollingSphere } from '../src/model/RollingSphere.js';

/**
 * Test the gravity damping and jump height fixes
 */
class GravityTest {
    constructor() {
        // Test different gravity modes
        this.gravityModes = {
            'Standard': new THREE.Vector3(0, -15, 0),
            'Spherical': new THREE.Vector3(0, -15, 0), // Would be directional towards sphere center
            'Box': new THREE.Vector3(0, -15, 0) // Could have directional gravity
        };
        
        this.testResults = {};
    }
    
    /**
     * Test gravity damping behavior
     */
    testGravityDamping() {
        console.log('Testing Gravity Damping Fix...');
        
        for (const [modeName, gravity] of Object.entries(this.gravityModes)) {
            console.log(`\nTesting ${modeName} gravity:`);
            
            const sphere = new RollingSphere();
            sphere.gravity.copy(gravity);
            
            // Simulate falling from height
            sphere.setPosition(new THREE.Vector3(0, 10, 0));
            sphere.isGrounded = false;
            sphere.velocity.set(5, -2, 0); // Horizontal + vertical velocity
            
            const initialVelocity = sphere.getVelocity();
            
            // Apply horizontal input while falling
            const testInput = {
                moveForward: true,
                moveBackward: false,
                moveLeft: false,
                moveRight: false,
                jumpPressed: false
            };
            
            // Update with horizontal input
            sphere.updateDesiredVelocity(testInput);
            sphere.updateVelocity(0.016); // ~60fps
            
            const finalVelocity = sphere.getVelocity();
            
            console.log(`Initial velocity: (${initialVelocity.x.toFixed(2)}, ${initialVelocity.y.toFixed(2)}, ${initialVelocity.z.toFixed(2)})`);
            console.log(`Final velocity: (${finalVelocity.x.toFixed(2)}, ${finalVelocity.y.toFixed(2)}, ${finalVelocity.z.toFixed(2)})`);
            
            // Check that vertical velocity wasn't damped by horizontal acceleration
            const verticalDiff = Math.abs(finalVelocity.y - initialVelocity.y);
            const horizontalDiff = Math.abs(finalVelocity.x - initialVelocity.x);
            
            console.log(`Vertical velocity change: ${verticalDiff.toFixed(4)}`);
            console.log(`Horizontal velocity change: ${horizontalDiff.toFixed(4)}`);
            
            // The vertical velocity should remain largely unchanged (except for gravity)
            // while horizontal velocity accelerates toward desired direction
            this.testResults[`${modeName}_gravity_damping`] = {
                verticalChange: verticalDiff,
                horizontalChange: horizontalDiff,
                testInput
            };
        }
    }
    
    /**
     * Test jump height calibration
     */
    testJumpHeight() {
        console.log('\n\nTesting Jump Height Calibration...');
        
        for (const [modeName, gravity] of Object.entries(this.gravityModes)) {
            console.log(`\nTesting ${modeName} gravity:`);
            
            const sphere = new RollingSphere();
            sphere.gravity.copy(gravity);
            sphere.isGrounded = true;
            
            // Calculate expected jump height
            const jumpImpulse = sphere.calculateJumpImpulseForHeight(3);
            const expectedHeight = (jumpImpulse * jumpImpulse) / (2 * Math.abs(gravity.y));
            
            console.log(`Calculated jump impulse: ${jumpImpulse.toFixed(2)}`);
            console.log(`Expected max height: ${expectedHeight.toFixed(2)} units`);
            console.log(`Target height: 3.0 units`);
            console.log(`Error margin: ${Math.abs(expectedHeight - 3.0).toFixed(4)} units`);
            
            // Simulate jump
            sphere.executeJump();
            const initialY = sphere.getPosition().y;
            
            // Simulate flight until peak
            let maxHeight = initialY;
            let time = 0;
            
            while (sphere.velocity.y > 0) {
                sphere.updateVelocity(0.016);
                sphere.velocity.addScaledVector(gravity, 0.016);
                const currentY = sphere.getPosition().y;
                if (currentY > maxHeight) {
                    maxHeight = currentY;
                }
                time += 0.016;
            }
            
            const actualHeightGained = maxHeight - initialY;
            console.log(`Actual peak height gain: ${actualHeightGained.toFixed(2)} units`);
            console.log(`Peak difference from expected: ${Math.abs(actualHeightGained - 3.0).toFixed(4)} units`);
            
            this.testResults[`${modeName}_jump_height`] = {
                calculatedImpulse: jumpImpulse,
                expectedHeight: expectedHeight,
                actualHeight: actualHeightGained,
                error: Math.abs(actualHeightGained - 3.0)
            };
        }
    }
    
    /**
     * Run all tests and summarize results
     */
    runAllTests() {
        console.log('=== RollingSphere Physics Tests ===\n');
        
        this.testGravityDamping();
        this.testJumpHeight();
        
        console.log('\n=== Test Summary ===');
        
        // Check gravity damping results
        let gravityDampingPassed = true;
        for (const [testName, result] of Object.entries(this.testResults)) {
            if (testName.includes('gravity_damping')) {
                // Vertical change should be minimal (gravity only), horizontal should show acceleration
                const verticalChange = result.verticalChange;
                gravityDampingPassed = gravityDampingPassed && (verticalChange < 0.1); // Small vertical change
            }
        }
        
        // Check jump height results
        let jumpHeightPassed = true;
        for (const [testName, result] of Object.entries(this.testResults)) {
            if (testName.includes('jump_height')) {
                jumpHeightPassed = jumpHeightPassed && (result.error < 0.1); // Within 0.1 units accuracy
            }
        }
        
        console.log(`Gravity Damping Fix: ${gravityDampingPassed ? 'PASSED' : 'FAILED'}`);
        console.log(`Jump Height Calibration: ${jumpHeightPassed ? 'PASSED ✓' : 'FAILED'}`);
        
        return {
            gravityDampingPassed,
            jumpHeightPassed,
            details: this.testResults
        };
    }
}

// Run tests if this file is executed directly
if (typeof window === 'undefined') {
    const test = new GravityTest();
    test.runAllTests();
}

export { GravityTest };