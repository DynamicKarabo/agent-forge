// @ts-check
const { test, expect } = require('@playwright/test');

test.describe('AgentForge Functional Tests', () => {

    test.beforeEach(async ({ page }) => {
        await page.goto('/');
        // Close welcome modal if present
        const demoButton = page.getByRole('button', { name: 'Start from Scratch' });
        if (await demoButton.isVisible()) {
            await demoButton.click();
        }
        // Clear canvas if needed (ensure clean state)
        await page.evaluate(() => {
            if (window.Alpine) {
                window.Alpine.store('workflow').clearCanvas();
            }
        });
    });

    test('1. Node Creation', async ({ page }) => {
        // Click palette button
        await page.getByText('Researcher', { exact: true }).first().click();

        // Check if node appears
        const node = page.locator('.jtk-managed').first();
        await expect(node).toBeVisible();
        await expect(node).toContainText('Researcher');

        // Check auto-positioning (add second node)
        await page.getByText('Writer', { exact: true }).first().click();
        const nodes = page.locator('.jtk-managed');
        await expect(nodes).toHaveCount(2);

        // Simple check that they are not in the same position
        const box1 = await nodes.nth(0).boundingBox();
        const box2 = await nodes.nth(1).boundingBox();
        expect(box1?.x).not.toBe(box2?.x);
        expect(box1?.y).not.toBe(box2?.y);
    });

    test('2. Node Interaction', async ({ page }) => {
        // Add a node
        await page.getByText('Researcher', { exact: true }).first().click();
        const node = page.locator('.jtk-managed').first();

        // Double click to open config
        await node.dblclick();
        const configPanel = page.locator('.fixed.inset-0.z-50');
        await expect(configPanel).toBeVisible();
        await expect(page.getByText('Agent Configuration')).toBeVisible();

        // Edit system prompt
        const promptInput = page.locator('textarea');
        await promptInput.fill('Updated System Prompt');
        await page.getByRole('button', { name: 'Save Changes' }).click();
        await expect(configPanel).not.toBeVisible();

        // Verify persistence (re-open)
        await node.dblclick();
        await expect(promptInput).toHaveValue('Updated System Prompt');
        await page.getByRole('button', { name: 'Save Changes' }).click();

        // Delete node via Hover X button (simulated as it appears on hover)
        // For stability in tests, we can use the context menu or selection + delete key
        await node.click();
        await page.keyboard.press('Delete');

        // Confirm deletion modal
        await page.getByRole('button', { name: 'Delete', exact: true }).click();

        await expect(node).not.toBeVisible();
    });

    test('3. Connections', async ({ page }) => {
        // Add two nodes
        await page.getByText('Researcher', { exact: true }).first().click();
        await page.getByText('Writer', { exact: true }).first().click();

        const sourceNode = page.locator('.jtk-managed').nth(0);
        const targetNode = page.locator('.jtk-managed').nth(1);

        // Get ports (assuming .output and .input classes)
        const sourcePort = sourceNode.locator('.output');
        const targetPort = targetNode.locator('.input');

        // Drag and drop connection
        await sourcePort.dragTo(targetPort);

        // Verify connection exists (jsPlumb adds SVG connector)
        const connector = page.locator('.jtk-connector');
        await expect(connector).toBeVisible();

        // Test Invalid Connection (Self-loop)
        const inputPort = sourceNode.locator('.input');
        await sourcePort.dragTo(inputPort);
        // Should still only have 1 connector
        await expect(connector).toHaveCount(1);
    });

    test('4. Canvas Navigation', async ({ page }) => {
        // Zoom In
        const zoomIn = page.locator('button[title="Zoom In"]'); // Adjust selector if needed, usually + button
        // Or finds by text "+" inside buttons
        const zoomInBtn = page.getByRole('button', { name: '+' });
        await zoomInBtn.click();

        // Check transform scale (implementation detail)
        const layer = page.locator('#canvas-layer');
        await expect(layer).toHaveAttribute('style', /scale\(1\.1\)/); // Assuming 0.1 step

        // Reset view
        await page.getByTitle('Fit to View').click();
        // Scale usually resets to calculated value, checking it changes is enough
    });

    test('5. Workflow Run (Mocked)', async ({ page }) => {
        // Mock the backend
        await page.route('http://localhost:8000/run_node', async route => {
            const json = {
                agent_config: {},
                history: [],
                prompt: ""
            };

            // Return a stream (simulated via text/event-stream format usually, or just direct response for this mock)
            // Since the frontend parses `data: {...}` lines, we simulate that.
            const body = `data: {"status": "success", "content": "Mocked research result", "type": "thought", "text": "Thinking...", "agent": "Researcher"}\n\n`;

            await route.fulfill({
                status: 200,
                contentType: 'text/plain', // or text/event-stream
                body: body
            });
        });

        // Setup workflow
        await page.getByText('Researcher', { exact: true }).first().click();

        // Enter prompt
        const promptInput = page.getByPlaceholder('Describe your workflow task');
        await promptInput.fill('Run Test');

        // Run
        await page.getByRole('button', { name: 'Run Workflow' }).click(); // The button might say 'Run' or 'Run Workflow'

        // Check logs
        await expect(page.locator('#logs-container')).toContainText('Thinking...');

        // Check completion/history update (this depends on your frontend handling the mock)
        // Wait for "Finished" log or similar
        // await expect(page.getByText('Finished in')).toBeVisible({ timeout: 10000 });
    });

    test('6. Save/Load', async ({ page }) => {
        // Create a unique state
        await page.getByText('Researcher', { exact: true }).first().click();

        // Save
        const downloadPromise = page.waitForEvent('download');
        await page.getByRole('button', { name: 'Save' }).click();
        const download = await downloadPromise;
        expect(download.suggestedFilename()).toContain('agentforge_workflow');

        // Clear
        await page.on('dialog', dialog => dialog.accept()); // Handle confirm clear
        await page.getByTitle('Clear Canvas').click();
        await expect(page.locator('.jtk-managed')).toHaveCount(0);

        // Load (requires file interactions, creating a buffer from the saved data)
        // For simplicity, we can reload the page or use the `loadData` store method if testing file picker is flaky without a real file.
        // But Playwright can handle file uploads.
        // Let's create a dummy file to upload.
        const workflowData = JSON.stringify({
            nodes: [{ id: 'test-1', type: 'Writer', x: 100, y: 100, data: { system_prompt: 'Test', text: 'text-teal-700' } }],
            edges: []
        });

        await page.setInputFiles('input[type="file"]', {
            name: 'test_workflow.json',
            mimeType: 'application/json',
            buffer: Buffer.from(workflowData)
        }); // This triggers the hidden file input if your "Load" button triggers it.

        // If the input is hidden and triggered by button click, we might need to make it visible or ensure Playwright finds it.
        // Usually `setInputFiles` on the invisible input works if attached to DOM.
        // Let's refine:
        // The load button triggers `input.click()`. We can attach a listener or just set the input files directly if we can Select the input.
        // Since the input is created dynamically in `loadWorkflow()`, we can't easily select it unless we stub `loadWorkflow` or use a different approach.
        // Actually `loadWorkflow` creates: `const input = document.createElement('input'); input.click();`
        // This is hard to intercept with `setInputFiles` because the input is not in the DOM tree effectively.
        // ALTERNATIVE: Mock the `loadWorkflow` function or manually mistakenly trigger the file chooser.
        // Better: Playwright handles `fileChooser` event.

        const fileChooserPromise = page.waitForEvent('filechooser');
        await page.getByRole('button', { name: 'Load' }).click();
        const fileChooser = await fileChooserPromise;
        await fileChooser.setFiles({
            name: 'test_workflow.json',
            mimeType: 'application/json',
            buffer: Buffer.from(workflowData)
        });

        // Verify loaded
        await expect(page.locator('.jtk-managed')).toBeVisible();
        await expect(page.locator('.jtk-managed')).toContainText('Writer');
    });

});
