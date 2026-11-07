const DATABASE_NAME = 'kalvikkan-documents';
const STORE_NAME = 'files';
const DATABASE_VERSION = 1;

function openDocumentDatabase(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DATABASE_NAME, DATABASE_VERSION);

    request.onupgradeneeded = () => {
      request.result.createObjectStore(STORE_NAME);
    };
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error || new Error('Could not open document storage.'));
  });
}

export async function saveDocumentFile(documentId: string, file: File): Promise<void> {
  const database = await openDocumentDatabase();

  await new Promise<void>((resolve, reject) => {
    const transaction = database.transaction(STORE_NAME, 'readwrite');
    transaction.objectStore(STORE_NAME).put(file, documentId);
    transaction.oncomplete = () => resolve();
    transaction.onerror = () => reject(transaction.error || new Error('Could not save uploaded document.'));
    transaction.onabort = () => reject(transaction.error || new Error('Document storage transaction was aborted.'));
  }).finally(() => database.close());
}

export async function getDocumentFile(documentId: string): Promise<Blob | null> {
  const database = await openDocumentDatabase();

  return new Promise<Blob | null>((resolve, reject) => {
    const transaction = database.transaction(STORE_NAME, 'readonly');
    const request = transaction.objectStore(STORE_NAME).get(documentId);
    request.onsuccess = () => resolve(request.result instanceof Blob ? request.result : null);
    request.onerror = () => reject(request.error || new Error('Could not load stored document.'));
    transaction.oncomplete = () => database.close();
    transaction.onerror = () => database.close();
    transaction.onabort = () => database.close();
  });
}
