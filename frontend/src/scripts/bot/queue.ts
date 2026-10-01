type Status = "ran" | "failed" | "queued";

interface Pending<T> {
  onReady: (data: T) => void;
  onFail: () => void;
}

export class ActionQueue<T> {
  private pending: Pending<T>[] = [];
  private settled: boolean | null = null;
  private data: T | null = null;

  isEmpty(): boolean {
    return this.pending.length === 0;
  }

  status(): boolean | null {
    return this.settled;
  }

  run(onReady: (data: T) => void, onFail: () => void): Status {
    if (this.settled === true && this.data !== null) {
      onReady(this.data);
      return "ran";
    }
    if (this.settled === false) {
      onFail();
      return "failed";
    }
    this.pending.push({ onReady, onFail });
    return "queued";
  }

  resolve(data: T): number {
    this.settled = true;
    this.data = data;
    return this.flush().map((item) => {
      item.onReady(data);
      return item;
    }).length;
  }

  reject(): number {
    this.settled = false;
    return this.flush().map((item) => {
      item.onFail();
      return item;
    }).length;
  }

  private flush(): Pending<T>[] {
    const queued = this.pending;
    this.pending = [];
    return queued;
  }
}
