/**
 * Jest Test Setup for DevSkyy Enterprise Platform
 * Global test configuration and utilities
 */
import 'jest';
declare global {
    namespace jest {
        interface Matchers<R> {
            toBeValidDate(): R;
            toBeValidUUID(): R;
            toHaveValidStructure(expected: Record<string, string>): R;
        }
    }
}
export declare const createMockAgent: (overrides?: Partial<import("@/types").Agent>) => {
    id: string;
    name: string;
    type: import("@/types").AgentType;
    status: import("@/types").AgentStatus;
    capabilities: string[];
    version: string;
    lastActive: Date;
    metadata: Record<string, unknown>;
};
export declare const createMockTask: (overrides?: Partial<import("@/types").AgentTask>) => {
    id: string;
    agentId: string;
    type: string;
    payload: Record<string, unknown>;
    status: import("@/types").TaskStatus;
    priority: import("@/types").TaskPriority;
    createdAt: Date;
    updatedAt: Date;
    completedAt?: Date;
    result?: import("@/types").TaskResult;
    error?: import("@/types").TaskError;
};
export declare const createMockUser: (overrides?: Partial<import("@/types").User>) => {
    id: string;
    username: string;
    email: string;
    role: import("@/types").UserRole;
    permissions: import("@/types").Permission[];
    isActive: boolean;
    lastLogin?: Date;
    createdAt: Date;
    updatedAt: Date;
};
export declare const clearTestDatabase: () => Promise<void>;
export declare const seedTestDatabase: () => Promise<void>;
export declare const waitFor: (ms: number) => Promise<void>;
export declare const waitForCondition: (condition: () => boolean | Promise<boolean>, timeout?: number, interval?: number) => Promise<void>;
export declare const createMockApiResponse: <T>(data: T, overrides?: Partial<import("@/types").ApiResponse<T>>) => {
    success: boolean;
    data: T;
    message?: string;
    error?: import("@/types").ApiError;
    metadata: import("@/types").ResponseMetadata;
};
export declare const expectToThrowAsync: (fn: () => Promise<unknown>, expectedError?: string | RegExp) => Promise<void>;
//# sourceMappingURL=setup.d.ts.map
