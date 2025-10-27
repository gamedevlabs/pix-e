export interface Asset {
    name?: string;
    className?: string;
    path?: string;

    title?: string;
    name?: string;
    type?: string;
    size?: number; // in bytes
    url?: string;
    thumbnailUrl?: string;
    previewUrl?: string;
    [key: string]: any;
}