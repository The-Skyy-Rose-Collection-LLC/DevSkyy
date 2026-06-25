import { Button } from '@skyyrose/storefront-ds'

export const Solid = () => <Button variant="solid">Shop Signature</Button>
export const Ghost = () => <Button variant="ghost">View Lookbook</Button>
export const AsLink = () => <Button as="a" href="#" variant="solid" size="lg">Pre-Order Now</Button>
export const Loading = () => <Button loading>Adding to Cart…</Button>
export const Disabled = () => <Button disabled>Sold Out</Button>
