export interface Asset {
    id?: number;
    name?: string;
    className?: string;
    path?: string;

    createdAt?: string;
    updatedAt?: string;

    title?: string;
    name?: string;
    type?: string;
    size?: number; // in bytes
    url?: string;
    thumbnailUrl?: string;
    previewUrl?: string;
    [key: string]: any;
}